"""
Seitenmodul für Inventar
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import random
from utils import (
    format_time_ago, get_severity_color, get_priority_color, get_risk_color,
    get_status_color, calculate_inventory_status, calculate_capacity_status,
    format_duration_minutes, get_department_color, get_system_status,
    get_metric_severity_for_load, get_metric_severity_for_count, get_metric_severity_for_free,
    get_explanation_score_color, calculate_days_until_stockout, calculate_reorder_suggestion,
    calculate_daily_consumption_from_activity
)
from ui.components import render_badge, render_empty_state


def render(db, sim, get_cached_alerts=None, get_cached_recommendations=None, get_cached_capacity=None):
    """Rendert die Inventar-Seite"""
    # Hole Simulationszustand für Aktivitäts-basierte Berechnungen
    sim_metrics = sim.get_current_metrics()
    capacity_data = db.get_capacity_overview()
    
    inventory = db.get_inventory_status()
    
    if inventory:
        # 1. Nachfüllvorschläge
        st.markdown("---")
        st.markdown("#### Nachfüllvorschläge")
        st.markdown("")  # Abstand
        
        # Berechne Verbrauchsraten und Nachfüllvorschläge für alle Artikel
        restock_suggestions = []
        for item in inventory:
            # Berechne Verbrauchsrate basierend auf Historie und Aktivität
            # Fallback falls Methode nicht verfügbar (z.B. bei gecachtem db-Objekt)
            if hasattr(db, 'calculate_inventory_consumption_rate'):
                consumption_rate_data = db.calculate_inventory_consumption_rate(
                    item_id=item['id'],
                    sim_state={
                        'ed_load': sim_metrics.get('ed_load', 65.0),
                        'beds_occupied': sum([c.get('occupied_beds', 0) for c in capacity_data])
                    }
                )
                daily_consumption_rate = consumption_rate_data['daily_rate']
            else:
                # Fallback: Berechne direkt basierend auf Aktivität
                daily_consumption_rate = calculate_daily_consumption_from_activity(
                    item=item,
                    ed_load=sim_metrics.get('ed_load', 65.0),
                    beds_occupied=sum([c.get('occupied_beds', 0) for c in capacity_data]),
                    capacity_data=capacity_data
                )
            
            # Berechne Tage bis Engpass
            days_until_stockout = calculate_days_until_stockout(
                current_stock=item['current_stock'],
                daily_consumption_rate=daily_consumption_rate
            )
            
            # Berechne Nachfüllvorschlag
            reorder_suggestion = calculate_reorder_suggestion(
                item=item,
                daily_consumption_rate=daily_consumption_rate,
                days_until_stockout=days_until_stockout
            )
            
            # Nur Artikel mit hoher oder mittlerer Priorität anzeigen
            if reorder_suggestion['priority'] in ['hoch', 'mittel']:
                restock_suggestions.append({
                    'item': item,
                    'consumption_rate': daily_consumption_rate,
                    'days_until_stockout': days_until_stockout,
                    'suggestion': reorder_suggestion
                })
        
        # Sortiere nach Priorität
        restock_suggestions.sort(key=lambda x: {'hoch': 1, 'mittel': 2, 'niedrig': 3}[x['suggestion']['priority']])
        
        if restock_suggestions:
            for suggestion_data in restock_suggestions:
                item = suggestion_data['item']
                suggestion = suggestion_data['suggestion']
                consumption_rate = suggestion_data['consumption_rate']
                days_until_stockout = suggestion_data['days_until_stockout']
                
                priority_color = get_severity_color(suggestion['priority'])
                
                # Formatiere Bestelltermin
                order_by_info = ""
                if suggestion['order_by_days'] is not None:
                    if suggestion['order_by_days'] == 0:
                        order_by_info = " • <span style='color: #DC2626; font-weight: 600;'>SOFORT bestellen</span>"
                    elif suggestion['order_by_days'] == 1:
                        order_by_info = f" • Bestellen bis: <span style='color: {priority_color}; font-weight: 600;'>morgen</span>"
                    else:
                        order_by_info = f" • Bestellen bis: <span style='color: {priority_color}; font-weight: 600;'>{suggestion['order_by_days']} Tage</span>"
                
                # Tage bis Engpass Info
                days_info = ""
                if days_until_stockout is not None:
                    days_info = f" • {days_until_stockout:.1f} Tage bis Engpass"
                
                # Verbrauchsrate Info
                consumption_info = f" • Verbrauch: {consumption_rate:.1f} {item['unit']}/Tag"
                
                st.markdown(f"""
                <div style="background: #f9fafb; padding: 1rem; border-radius: 6px; margin-bottom: 0.5rem; border-left: 3px solid {priority_color};">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">{item['item_name']}</div>
                            <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem;">
                                {item.get('department', 'N/A')}{days_info}{consumption_info}
                            </div>
                            <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem;">
                                Aktuell: {item['current_stock']} {item['unit']} → Vorgeschlagen: {suggestion['suggested_qty']} {item['unit']}
                            </div>
                            <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem; font-style: italic;">
                                {suggestion['reasoning']}{order_by_info}
                            </div>
                        </div>
                        <div style="font-weight: 600; color: {priority_color}; margin-left: 1rem;">
                            +{suggestion['suggested_qty'] - item['current_stock']} {item['unit']}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(render_empty_state("📦", "Keine Nachfüllvorschläge", "Alle Lagerbestände sind ausreichend"), unsafe_allow_html=True)
        
        # 2. Lagerrisiko
        st.markdown("---")
        st.markdown("### Lagerrisiko")
        st.markdown("")  # Abstand
        
        # Verwende echte Inventory-Daten aus der DB mit präzisen Berechnungen
        inventory_materials = []
        for item in inventory:
            stock_percent = (item['current_stock'] / item['max_capacity']) * 100 if item['max_capacity'] > 0 else 0
            threshold_percent = (item['min_threshold'] / item['max_capacity']) * 100 if item['max_capacity'] > 0 else 0
            
            # Berechne Verbrauchsrate
            # Fallback falls Methode nicht verfügbar (z.B. bei gecachtem db-Objekt)
            if hasattr(db, 'calculate_inventory_consumption_rate'):
                consumption_rate_data = db.calculate_inventory_consumption_rate(
                    item_id=item['id'],
                    sim_state={
                        'ed_load': sim_metrics.get('ed_load', 65.0),
                        'beds_occupied': sum([c.get('occupied_beds', 0) for c in capacity_data])
                    }
                )
                daily_consumption_rate = consumption_rate_data['daily_rate']
            else:
                # Fallback: Berechne direkt basierend auf Aktivität
                daily_consumption_rate = calculate_daily_consumption_from_activity(
                    item=item,
                    ed_load=sim_metrics.get('ed_load', 65.0),
                    beds_occupied=sum([c.get('occupied_beds', 0) for c in capacity_data]),
                    capacity_data=capacity_data
                )
            
            # Berechne Tage bis Engpass (präzise)
            days_until_stockout = calculate_days_until_stockout(
                current_stock=item['current_stock'],
                daily_consumption_rate=daily_consumption_rate
            )
            
            # Risiko auf Deutsch zuweisen basierend auf präziser Berechnung
            if days_until_stockout is not None:
                if days_until_stockout <= 2:
                    risk_level = "hoch"
                elif days_until_stockout <= 7:
                    risk_level = "mittel"
                else:
                    risk_level = "niedrig"
            elif item['current_stock'] < item['min_threshold']:
                risk_level = "mittel"
            else:
                risk_level = "niedrig"
            
            inventory_materials.append({
                'name': item['item_name'],
                'current_stock': item['current_stock'],
                'min_threshold': item['min_threshold'],
                'max_capacity': item['max_capacity'],
                'unit': item['unit'],
                'department': item.get('department', 'N/A'),
                'days_until_stockout': days_until_stockout,
                'risk_level': risk_level,
                'stock_percent': stock_percent,
                'threshold_percent': threshold_percent,
                'consumption_rate': daily_consumption_rate
            })

        # Nach Risiko sortieren (hoch zuerst)
        inventory_materials.sort(key=lambda x: {'hoch': 1, 'mittel': 2, 'niedrig': 3}[x['risk_level']])

        # Anzeige aller Materialien mit Risiko
        if inventory_materials:
            st.markdown("#### Materialien mit Risiko")
            st.markdown("")  # Abstand
            
            # Als formatierte Tabelle anzeigen
            for mat in inventory_materials:
                risk_color = get_severity_color(mat['risk_level'])
                risk_badge = render_badge(mat['risk_level'].upper(), mat['risk_level'])
                days_display = f"{mat['days_until_stockout']:.1f} Tage" if mat['days_until_stockout'] is not None else "N/V"
                consumption_display = f"{mat.get('consumption_rate', 0):.1f} {mat['unit']}/Tag"
                stock_percent = mat['stock_percent']
                threshold_percent = mat['threshold_percent']
                # Bestimme Farbe für Fortschrittsleiste basierend auf Risiko
                progress_color = risk_color if mat['risk_level'] in ['hoch', 'mittel'] else "#10B981"
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid {risk_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr 1fr; gap: 1rem; align-items: center;">
                        <div>
                            <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.25rem;">{mat['name']}</div>
                            <div style="font-size: 0.75rem; color: #6b7280;">{mat['department']}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Aktuell</div>
                            <div style="font-weight: 600; color: #1f2937;">{mat['current_stock']} {mat['unit']}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Mindestbestand</div>
                            <div style="font-weight: 600; color: #1f2937;">{mat['min_threshold']} {mat['unit']}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Maximaler Bestand</div>
                            <div style="font-weight: 600; color: #1f2937;">{mat['max_capacity']} {mat['unit']}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Verbrauch/Tag</div>
                            <div style="font-weight: 600; color: #1f2937;">{consumption_display}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #6b7280; margin-bottom: 0.25rem;">Tage bis Engpass</div>
                            <div style="font-weight: 600; color: {risk_color if mat['days_until_stockout'] else '#6b7280'};">{days_display}</div>
                        </div>
                        <div>
                            {risk_badge}
                        </div>
                    </div>
                    <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid #e5e7eb;">
                        <div style="position: relative; background: #e5e7eb; height: 6px; border-radius: 3px; overflow: visible;">
                            <div style="background: {progress_color}; height: 100%; width: {min(100, stock_percent)}%; transition: width 0.3s ease; border-radius: 3px;"></div>
                            <div style="position: absolute; left: {min(100, threshold_percent)}%; top: -2px; width: 2px; height: 10px; background: #DC2626; z-index: 10; border-radius: 1px;"></div>
                        </div>
                        <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem; text-align: right;">
                            {stock_percent:.1f}% des maximalen Bestands
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(render_empty_state("📦", "Keine Materialien mit Risiko", "Alle Lagerbestände sind ausreichend"), unsafe_allow_html=True)
        
        # 3. Bestandsverlauf (als Liniendiagramm)
        st.markdown("---")
        st.markdown("### Bestandsverlauf")
        
        # Generiere simulierte historische Daten für die letzten 14 Tage
        dates = [datetime.now() - timedelta(days=x) for x in range(14, -1, -1)]
        
        # Erstelle Liniendiagramm für jeden Artikel
        fig = go.Figure()
        
        # Farben für verschiedene Artikel
        colors = px.colors.qualitative.Set3
        
        for idx, item in enumerate(inventory):
            # Simuliere historische Bestandsdaten
            # Starte mit einem zufälligen Wert nahe dem aktuellen Bestand
            base_stock = item['current_stock']
            historical_stocks = []
            
            # Generiere realistische Verlaufsdaten
            for i, date in enumerate(dates):
                # Simuliere Schwankungen mit einem Trend
                variation = random.uniform(-0.15, 0.15)  # ±15% Variation
                trend = (14 - i) / 14 * 0.1  # Leichter Trend zum aktuellen Wert
                stock_value = max(0, int(base_stock * (1 + variation + trend)))
                historical_stocks.append(stock_value)
            
            # Berechne Auslastung in Prozent
            utilization = [(stock / item['max_capacity']) * 100 if item['max_capacity'] > 0 else 0 for stock in historical_stocks]
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=utilization,
                mode='lines+markers',
                name=item['item_name'],
                line=dict(color=colors[idx % len(colors)], width=2),
                marker=dict(size=4)
            ))
        
        fig.update_layout(
            title="",
            xaxis_title="Datum",
            yaxis_title="Auslastung (%)",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Keine Bestandsdaten verfügbar")

"""
Styling und CSS für HospitalFlow
Professionelles Design-System
"""
import streamlit as st


def apply_custom_styles():
    """Wende benutzerdefiniertes CSS-Styling an"""
    st.markdown("""
    <style>
        /* Professionelle Typografie */
        * {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, 'Helvetica Neue', Arial, sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-weight: 600;
            letter-spacing: -0.02em;
            color: #111827;
            line-height: 1.2;
        }
        
        /* Hauptcontainer - professioneller Abstand */
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1600px;
        }
        
        /* Professioneller Sticky Header */
        .sticky-header {
            position: sticky;
            top: -1rem;
            z-index: 999;
            background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
            border-bottom: 2px solid #e5e7eb;
            padding: 1.25rem 0;
            margin: -1rem 0 2rem 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            backdrop-filter: blur(10px);
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1600px;
            margin: 0 auto;
            padding: 0 2rem;
        }
        
        .header-title {
            font-size: 1.625rem;
            font-weight: 700;
            color: #4f46e5;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            letter-spacing: -0.025em;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.8);
        }
        
        /* Professioneller Seiten-Header */
        .page-header {
            margin-bottom: 2.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .page-title {
            font-size: 2.25rem;
            font-weight: 700;
            color: #111827;
            margin: 0 0 0.5rem 0;
            letter-spacing: -0.03em;
        }
        
        .page-subtitle {
            font-size: 0.9375rem;
            color: #6b7280;
            margin: 0;
            font-weight: 400;
        }
        
        /* Professionelle Metrik-Karten */
        .metric-card {
            background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
            padding: 1.75rem;
            border-radius: 16px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
            border: 1px solid #e5e7eb;
            border-left: 4px solid #667eea;
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            opacity: 0;
            transition: opacity 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.06);
        }
        
        .metric-card:hover::before {
            opacity: 1;
        }
        
        .metric-value {
            font-size: 2.25rem;
            font-weight: 700;
            color: #111827;
            margin: 0.75rem 0;
            line-height: 1.1;
            letter-spacing: -0.02em;
        }
        
        .metric-label {
            font-size: 0.8125rem;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 600;
        }
        
        /* Professionelle Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.4375rem 0.875rem;
            border-radius: 12px;
            font-size: 0.6875rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            line-height: 1;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
        
        /* Professionelle Tabellen */
        .dataframe {
            border-radius: 12px;
            overflow: hidden;
            font-size: 0.875rem;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        /* Professionelle Leere Zustände */
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            color: #9ca3af;
            background: linear-gradient(to bottom, #fafbfc 0%, #f9fafb 100%);
            border-radius: 16px;
            border: 2px dashed #d1d5db;
            margin: 2rem 0;
        }
        
        .empty-state-icon {
            font-size: 4rem;
            margin-bottom: 1.25rem;
            opacity: 0.4;
            filter: grayscale(20%);
        }
        
        .empty-state-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: #4b5563;
            margin-bottom: 0.75rem;
            letter-spacing: -0.01em;
        }
        
        .empty-state-text {
            font-size: 0.9375rem;
            color: #9ca3af;
            line-height: 1.6;
        }
        
        /* Professioneller Footer */
        .footer {
            margin-top: 4rem;
            padding: 3rem 0 2rem 0;
            border-top: 2px solid #e5e7eb;
            background: linear-gradient(to bottom, #fafbfc 0%, #ffffff 100%);
        }
        
        .footer-content {
            max-width: 1600px;
            margin: 0 auto;
            padding: 0 2rem;
        }
        
        /* Professionelle Legende */
        .legend {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            padding: 1rem;
            background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            font-size: 0.75rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.625rem;
            padding: 0.25rem 0;
        }
        
        /* Professioneller Zeitstempel */
        .timestamp {
            font-size: 0.75rem;
            color: #6b7280;
            font-weight: 500;
            letter-spacing: 0.02em;
        }
        
        /* Professionelle Karten */
        .info-card {
            background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        }
        
        .info-card:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            transform: translateY(-1px);
        }
        
        /* Professionelle Buttons */
        .stButton > button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        /* Professionelle Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
            border-right: 1px solid #e5e7eb;
        }
        
        /* Streamlit Standardelemente ausblenden */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Professionelle Lesbarkeit */
        p {
            line-height: 1.7;
            color: #374151;
        }
        
        /* Bessere Spaltenabstände */
        [data-testid="column"] {
            padding: 0 1rem;
        }
        
        /* Professionelle Abschnittstrenner */
        hr {
            border: none;
            border-top: 1px solid #e5e7eb;
            margin: 2rem 0;
        }
        
        /* Sanftes Scrollen */
        html {
            scroll-behavior: smooth;
        }
        
        /* Professionelle Eingabefelder */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 1px solid #d1d5db;
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* Professionelle Selectboxen */
        .stSelectbox > div > div {
            border-radius: 8px;
        }
        
        /* Ladezustände */
        .stSpinner > div {
            border-color: #667eea transparent transparent transparent;
        }
    </style>
    """, unsafe_allow_html=True)


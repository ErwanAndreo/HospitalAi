# HospitalFlow - Hospital Operations Dashboard

A modern, clean MVP dashboard for hospital staff built with Streamlit and SQLite. HospitalFlow provides real-time metrics, short-term predictions, alerts, recommendations, and comprehensive operational oversight—all using aggregated data only (no personal information).

## Features

### Core Functionality

- **Live Metrics**: Real-time monitoring of key hospital metrics with time-series visualization
- **5-15 Minute Predictions**: AI-powered short-term forecasts for patient arrivals, bed demand, and resource needs
- **Alerts System**: Severity-based alerts (high/medium/low) with acknowledgment workflow
- **Recommendations**: Human-in-the-loop AI recommendations with accept/reject functionality
- **Audit Log**: Complete audit trail of all system actions and changes
- **Transport Management**: Track and manage patient, equipment, and specimen transport requests
- **Inventory Monitoring**: Real-time inventory status with low-stock alerts
- **Device Maintenance Risk**: Risk assessment for medical device maintenance scheduling
- **Discharge Planning**: Aggregated discharge planning metrics by department
- **Capacity Overview**: Comprehensive bed capacity and utilization tracking

### UI/UX Highlights

- **Modern Design**: Clean, professional interface with custom styling (not default Streamlit)
- **Consistent Design System**: Unified spacing, typography, icons, and color palette
- **Top Header + Left Navigation**: Intuitive multi-page navigation
- **Metric Cards**: Visual metric cards with clear hierarchy
- **Pill Badges**: Color-coded severity/priority/status indicators
- **Plotly Charts**: Interactive, publication-quality visualizations
- **Microcopy**: Helpful hints and empty states throughout
- **Keyboard-Friendly**: Thoughtful defaults and accessible controls

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run app.py
   ```

4. **Access the dashboard**:
   The app will open automatically in your browser at `http://localhost:8501`

## Project Structure

```
HospitalFlow AI/
├── app.py              # Main Streamlit application
├── db.py               # SQLite database operations
├── utils.py            # Utility functions (predictions, formatting)
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── hospitalflow.db    # SQLite database (created automatically)
```

## Usage

### Navigation

Use the left sidebar to navigate between different sections:

- **Dashboard**: Overview with key metrics and recent alerts/recommendations
- **Live Metrics**: Real-time metrics with time-series charts
- **Predictions**: 5-15 minute forecasts with confidence scores
- **Alerts**: Active alerts with severity filtering and acknowledgment
- **Recommendations**: Review and accept/reject AI recommendations
- **Transport**: Manage transport requests by status
- **Inventory**: Monitor inventory levels with low-stock alerts
- **Device Maintenance**: Risk assessment for medical devices
- **Discharge Planning**: Aggregated discharge metrics by department
- **Capacity Overview**: Bed capacity and utilization tracking
- **Audit Log**: Complete system activity log

### Key Interactions

1. **Accepting/Rejecting Recommendations**:
   - Navigate to "Recommendations"
   - Enter action taken or rejection reason
   - Click "Accept" or "Reject"
   - Action is logged in audit trail

2. **Acknowledging Alerts**:
   - Navigate to "Alerts"
   - Click "Acknowledge" on any alert
   - Alert status updates immediately

3. **Filtering Data**:
   - Most pages include filter options (severity, department, status)
   - Use dropdowns to narrow down views

4. **Refreshing Data**:
   - Click the "🔄 Refresh Data" button in the sidebar
   - Or refresh the browser page

## Data Model

All data is **aggregated only**—no personal information is stored or displayed. The database includes:

- Metrics (counts, averages, percentages)
- Predictions (forecasted values)
- Alerts (system-generated notifications)
- Recommendations (AI-suggested actions)
- Transport requests (location-to-location)
- Inventory (item counts and thresholds)
- Device maintenance (equipment status)
- Discharge planning (department-level aggregates)
- Capacity (bed counts and utilization)
- Audit log (action history)

## Technical Details

- **Framework**: Streamlit 1.28+
- **Database**: SQLite (file-based, no setup required)
- **Visualization**: Plotly Express and Graph Objects
- **Data Processing**: Pandas
- **Python Version**: 3.8+

## Customization

### Adding New Metrics

Edit `db.py` to add new metric types or modify the schema. Update `app.py` to display new metrics in the UI.

### Modifying Predictions

Adjust prediction logic in `utils.py` functions like `generate_short_term_prediction()` and `calculate_prediction_confidence()`.

### Styling

Custom CSS is embedded in `app.py`. Modify the `<style>` block to change colors, spacing, or typography.

## Limitations

This is an MVP with the following constraints:

- **Sample Data**: Database is seeded with sample data on first run
- **No Real-time Updates**: Data refreshes on page reload or manual refresh
- **Local Only**: SQLite database is file-based (not suitable for multi-user production)
- **No Authentication**: No user authentication or role-based access control
- **Static Predictions**: Predictions are based on simple algorithms (not ML models)

## Future Enhancements

Potential improvements for production:

- Real-time data integration (APIs, message queues)
- Machine learning models for predictions
- User authentication and authorization
- Multi-user support with PostgreSQL
- Email/SMS notifications for critical alerts
- Export functionality (PDF reports, CSV exports)
- Mobile-responsive design improvements

## License

This project is provided as-is for demonstration purposes.

## Support

For issues or questions, please refer to the code comments or Streamlit documentation.

---

**Built with ❤️ for hospital staff**

# Updated Tue Dec 23 15:43:36 CET 2025

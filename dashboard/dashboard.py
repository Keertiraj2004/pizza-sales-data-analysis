import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px

# Load Dataset
df = pd.read_csv("../data/pizza_sales.csv")

df['order_date'] = pd.to_datetime(df['order_date'], dayfirst=True)

df['month'] = df['order_date'].dt.month
df['day'] = df['order_date'].dt.day_name()

# Correct day order
day_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

# Dash App
app = dash.Dash(__name__)

# Sidebar
sidebar = html.Div(
    [
        html.H2("Filters"),

        html.Label("Pizza Category"),
        dcc.Dropdown(
            id="category_filter",
            options=[{'label': i, 'value': i} for i in df['pizza_category'].unique()],
            multi=True
        ),

        html.Br(),

        html.Label("Pizza Size"),
        dcc.Dropdown(
            id="size_filter",
            options=[{'label': i, 'value': i} for i in df['pizza_size'].unique()],
            multi=True
        ),
    ],
    style={
        "width": "20%",
        "padding": "20px",
        "backgroundColor": "#2c3e50",
        "color": "white",
        "height": "100vh",
        "position": "fixed"
    }
)

# Main Content
content = html.Div(
    [

    html.H1("Pizza Sales Dashboard", style={'textAlign': 'center'}),

    # Selected Day Indicator
    html.Div(id="selected_day_indicator", style={
        'textAlign': 'center',
        'marginBottom': '5px',
        'color': '#e74c3c',
        'fontWeight': 'bold',
        'fontSize': '16px',
        'minHeight': '24px'
    }),

    # Reset Button
    html.Button(
        "Reset Day Filter",
        id="reset_day",
        n_clicks=0,
        style={
            "marginBottom": "20px",
            "padding": "8px 16px",
            "backgroundColor": "#34495e",
            "color": "white",
            "border": "none",
            "cursor": "pointer"
        }
    ),

    html.Div(id="kpi_cards", style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(5,1fr)',
        'gap': '10px'
    }),

    html.Br(),

    html.Div([
        dcc.Graph(id="daily_chart"),
        dcc.Graph(id="monthly_chart")
    ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr'}),

    html.Div([
        dcc.Graph(id="category_chart"),
        dcc.Graph(id="size_chart")
    ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr'}),

    dcc.Graph(id="funnel_chart"),

    html.H3("Top 5 Best Sellers"),

    html.Div([
        dcc.Graph(id="top5_revenue_chart"),
        dcc.Graph(id="top5_quantity_chart"),
        dcc.Graph(id="top5_orders_chart")
    ]),

    html.H3("Bottom 5 Worst Sellers"),

    html.Div([
        dcc.Graph(id="bottom5_revenue_chart"),
        dcc.Graph(id="bottom5_quantity_chart"),
        dcc.Graph(id="bottom5_orders_chart")
    ]),

    # Store to track the last reset click count and selected day
    dcc.Store(id="last_reset_clicks", data=0),
    dcc.Store(id="selected_day_store", data=None),

    ],

    style={"marginLeft": "22%", "padding": "20px"}
)

app.layout = html.Div([sidebar, content])


# --- Callback 1: Update the selected day store ---
@app.callback(
    Output("selected_day_store", "data"),
    Output("last_reset_clicks", "data"),
    Input("daily_chart", "clickData"),
    Input("reset_day", "n_clicks"),
    State("last_reset_clicks", "data"),
    State("selected_day_store", "data"),
)
def update_selected_day(clickData, reset_clicks, last_reset, current_day):
    ctx = dash.callback_context

    if not ctx.triggered:
        return None, last_reset

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Reset button was clicked (new click)
    if trigger_id == "reset_day" and reset_clicks > last_reset:
        return None, reset_clicks

    # Bar in daily chart was clicked
    if trigger_id == "daily_chart" and clickData:
        clicked_day = clickData['points'][0]['x']
        # Toggle: clicking same day again deselects it
        if clicked_day == current_day:
            return None, last_reset
        return clicked_day, last_reset

    return current_day, last_reset


# --- Callback 2: Show selected day indicator ---
@app.callback(
    Output("selected_day_indicator", "children"),
    Input("selected_day_store", "data"),
)
def update_indicator(selected_day):
    if selected_day:
        return f"📅 Filtered by: {selected_day}  (click the same bar or Reset to clear)"
    return ""


# --- Callback 3: Update all charts and KPIs ---
@app.callback(
    [
        Output("kpi_cards", "children"),
        Output("daily_chart", "figure"),
        Output("monthly_chart", "figure"),
        Output("category_chart", "figure"),
        Output("size_chart", "figure"),
        Output("funnel_chart", "figure"),
        Output("top5_revenue_chart", "figure"),
        Output("top5_quantity_chart", "figure"),
        Output("top5_orders_chart", "figure"),
        Output("bottom5_revenue_chart", "figure"),
        Output("bottom5_quantity_chart", "figure"),
        Output("bottom5_orders_chart", "figure")
    ],
    [
        Input("category_filter", "value"),
        Input("size_filter", "value"),
        Input("selected_day_store", "data"),
    ]
)
def update_dashboard(category, size, selected_day):

    filtered_df = df.copy()

    if category:
        filtered_df = filtered_df[filtered_df['pizza_category'].isin(category)]

    if size:
        filtered_df = filtered_df[filtered_df['pizza_size'].isin(size)]

    if selected_day:
        filtered_df = filtered_df[filtered_df['day'] == selected_day]

    # KPI Calculations
    total_revenue = filtered_df['total_price'].sum()
    total_orders = filtered_df['order_id'].nunique()
    total_pizzas = filtered_df['quantity'].sum()

    avg_order_value = total_revenue / total_orders if total_orders else 0
    avg_pizzas_per_order = total_pizzas / total_orders if total_orders else 0

    kpi_cards = [

        html.Div(["Total Revenue", html.Br(), f"${total_revenue:,.0f}"],
                 style={'backgroundColor': '#e74c3c', 'padding': '20px', 'borderRadius': '10px', 'color': 'white', 'textAlign': 'center'}),

        html.Div(["Avg Order Value", html.Br(), f"${avg_order_value:,.2f}"],
                 style={'backgroundColor': '#3498db', 'padding': '20px', 'borderRadius': '10px', 'color': 'white', 'textAlign': 'center'}),

        html.Div(["Total Pizzas Sold", html.Br(), total_pizzas],
                 style={'backgroundColor': '#f39c12', 'padding': '20px', 'borderRadius': '10px', 'color': 'white', 'textAlign': 'center'}),

        html.Div(["Total Orders", html.Br(), total_orders],
                 style={'backgroundColor': '#2ecc71', 'padding': '20px', 'borderRadius': '10px', 'color': 'white', 'textAlign': 'center'}),

        html.Div(["Avg Pizzas / Order", html.Br(), f"{avg_pizzas_per_order:.2f}"],
                 style={'backgroundColor': '#9b59b6', 'padding': '20px', 'borderRadius': '10px', 'color': 'white', 'textAlign': 'center'})
    ]

    # Daily Chart — highlight selected day
    daily = filtered_df.groupby('day')['order_id'].nunique().reindex(day_order).reset_index()

    if selected_day:
        daily['color'] = daily['day'].apply(lambda d: '#e74c3c' if d == selected_day else '#636efa')
        fig_daily = px.bar(daily, x='day', y='order_id', title="Daily Orders (click a bar to filter)",
                           color='color', color_discrete_map='identity')
    else:
        fig_daily = px.bar(daily, x='day', y='order_id', title="Daily Orders (click a bar to filter)")

    fig_daily.update_layout(showlegend=False)

    # Monthly Chart
    monthly = filtered_df.groupby('month')['order_id'].nunique().reset_index()
    fig_month = px.line(monthly, x='month', y='order_id', title="Monthly Orders")

    # Category Chart
    category_sales = filtered_df.groupby('pizza_category')['total_price'].sum().reset_index()
    fig_category = px.pie(category_sales, names='pizza_category', values='total_price', title="Sales by Category")

    # Size Chart
    size_sales = filtered_df.groupby('pizza_size')['total_price'].sum().reset_index()
    fig_size = px.pie(size_sales, names='pizza_size', values='total_price', title="Sales by Size")

    # Funnel Chart
    category_qty = filtered_df.groupby('pizza_category')['quantity'].sum().reset_index()
    fig_funnel = px.funnel(category_qty, x='quantity', y='pizza_category', title="Total Pizza Sold by Category")

    # Top 5
    top5_rev = filtered_df.groupby('pizza_name')['total_price'].sum().sort_values(ascending=False).head(5).reset_index()
    fig_top5_rev = px.bar(top5_rev, x='pizza_name', y='total_price', title="Top 5 by Revenue")

    top5_qty = filtered_df.groupby('pizza_name')['quantity'].sum().sort_values(ascending=False).head(5).reset_index()
    fig_top5_qty = px.bar(top5_qty, x='pizza_name', y='quantity', title="Top 5 by Quantity")

    top5_ord = filtered_df.groupby('pizza_name')['order_id'].nunique().sort_values(ascending=False).head(5).reset_index()
    fig_top5_ord = px.bar(top5_ord, x='pizza_name', y='order_id', title="Top 5 by Orders")

    # Bottom 5
    bottom5_rev = filtered_df.groupby('pizza_name')['total_price'].sum().sort_values().head(5).reset_index()
    fig_bottom5_rev = px.bar(bottom5_rev, x='pizza_name', y='total_price', title="Bottom 5 by Revenue")

    bottom5_qty = filtered_df.groupby('pizza_name')['quantity'].sum().sort_values().head(5).reset_index()
    fig_bottom5_qty = px.bar(bottom5_qty, x='pizza_name', y='quantity', title="Bottom 5 by Quantity")

    bottom5_ord = filtered_df.groupby('pizza_name')['order_id'].nunique().sort_values().head(5).reset_index()
    fig_bottom5_ord = px.bar(bottom5_ord, x='pizza_name', y='order_id', title="Bottom 5 by Orders")

    return (
        kpi_cards, fig_daily, fig_month, fig_category, fig_size, fig_funnel,
        fig_top5_rev, fig_top5_qty, fig_top5_ord,
        fig_bottom5_rev, fig_bottom5_qty, fig_bottom5_ord
    )


if __name__ == "__main__":
    app.run(debug=True)

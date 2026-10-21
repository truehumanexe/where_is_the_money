import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_tornado_chart(
    salaries: np.ndarray,
    population: np.ndarray,
    wealth: np.ndarray,
    population_title: str = "Population",
    bin_title: str = 'Salary',
    money_title: str = "USD",
    chart_title: str = "",
    use_log: bool = False,
    lower_salary_boundary = 10000,
    upper_salary_boundary = 1000000,
) -> go.Figure:
  """Creates a centered mirrored horizontal bar chart (tornado chart)

  using a 3-column layout with a bottom-center "Salaries" label.
  """
  # Format numeric salaries if needed
  if pd.api.types.is_numeric_dtype(salaries):
    salaries = np.array([format_to_compact_integer_string(s, lower_salary_boundary, upper_salary_boundary) for s in salaries])

  # Padding categories at the top and bottom for visual breathing room
  padded_salaries = np.insert(np.append(salaries, ""), 0, "")
  baseline = 1 if use_log else 0
  padded_pop = np.insert(np.append(population, baseline), 0, baseline)
  padded_wealth = np.insert(np.append(wealth, baseline), 0, baseline)

  # Create 3 columns: [Population, Center Labels, Wealth]
  fig = make_subplots(
      rows=1,
      cols=3,
      shared_yaxes=True,
      column_widths=[0.48, 0.04, 0.48],  # Middle column acts as the text gutter
      horizontal_spacing=0.02,
      subplot_titles=(population_title, bin_title, money_title),
  )

  # 1. Left Side: Population
  fig.add_trace(
      go.Bar(
          y=padded_salaries,
          x=padded_pop,
          orientation="h",
          marker_color="#2b5c8f",
      ),
      row=1,
      col=1,
  )

  # 2. Center Column: Text labels rendered as a scatter trace (perfectly centered)
  fig.add_trace(
      go.Scatter(
          x=[0] * len(padded_salaries),
          y=padded_salaries,
          mode="text",
          text=padded_salaries,
          textfont=dict(size=11, family="monospace", color="#333333"),
          hoverinfo="none",
      ),
      row=1,
      col=2,
  )

  # 3. Right Side: Wealth
  fig.add_trace(
      go.Bar(
          y=padded_salaries,
          x=padded_wealth,
          orientation="h",
          marker_color="#b22222",
      ),
      row=1,
      col=3,
  )

  # Axis configuration dictionary based on scale type
  if use_log:
    x_config_left = dict(
        type="log", autorange="reversed", dtick=1, showgrid=True
    )
    x_config_right = dict(type="log", dtick=1, showgrid=True)
  else:
    x_config_left = dict(
        type="linear", autorange="reversed", showgrid=True, zeroline=True
    )
    x_config_right = dict(
        type="linear", showgrid=True, zeroline=True
    )

  # Apply X-Axis configurations to outer columns
  fig.update_xaxes(row=1, col=1, **x_config_left)
  fig.update_xaxes(row=1, col=3, **x_config_right)

  # Hide axes entirely for the center text column
  fig.update_xaxes(visible=False, row=1, col=2)
  fig.update_yaxes(visible=False, row=1, col=2)

  # Hide default Y-axis ticks on left and right subplots
  fig.update_yaxes(showticklabels=False, row=1, col=1)
  fig.update_yaxes(showticklabels=False, row=1, col=3)

  # Layout styling (removed the annotations list parameter here)
  fig.update_layout(
      title_text=chart_title,
      title_x=0.5,
      bargap=0.18,
      showlegend=False,
      template="plotly_white",
      margin=dict(l=60, r=60, t=80, b=70),
      height=650,
    #   autosize=False,
  )

  # Add the "Salaries" label safely without wiping out subplot titles
#   fig.add_annotation(
#       text="<b>Salaries</b>",
#       x=0.5,
#       y=-0.08,
#       xref="paper",
#       yref="paper",
#       showarrow=False,
#       xanchor="center",
#       yanchor="top",
#       font=dict(size=12, family="sans-serif", color="#333333"),
#   )

  return fig





def format_to_compact_integer_string(val: float, lower_bound = 10000, upper_bound = 1000000) -> str:
  """Converts a numerical input into a compact integer-only string

  representation (max 4 characters total, e.g., '500', '12K', '150K', '2M').
  No decimals are used; values are rounded to the nearest whole integer
  within their magnitude tier.
  """
  if np.isinf(val):
    return "Total"
  else:
    if val == 0 or np.isnan(val):
        return "0"

    sign = "-" if val < 0 else ""
    val = abs(val)

    # Use log base 10 to determine the order of magnitude
    exp = int(math.floor(math.log10(val)))
    tier = exp // 3  # 0 = ones, 1 = thousands (K), 2 = millions (M), etc.

    suffixes = ["", "K", "M", "B", "T", "P"]
    if tier >= len(suffixes):
        tier = len(suffixes) - 1

    # Scale down and round to the nearest whole integer
    scaled = val / (10 ** (tier * 3))
    rounded = int(round(scaled))

    boundary_indicator = '+' if val >= upper_bound else ' ' # blank space will allow consistent look when center aligned
    boundary_indicator = '-' if val <= lower_bound else boundary_indicator

    # Edge case: if rounding pushes a 3-digit number up to 1000, bump the tier
    if rounded >= 1000 and tier < len(suffixes) - 1:
        tier += 1
        scaled = val / (10 ** (tier * 3))
        rounded = int(np.floor(scaled))

    return f"{sign}{rounded}{suffixes[tier]}{boundary_indicator}"
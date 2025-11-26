"""
Excel Export with Conditional Formatting Module

This module handles exporting race data to Excel with color highlighting
applied only to rows corresponding to bet-worthy races.

Uses openpyxl for fine-grained control over cell formatting.
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime


# ===== COLOR CONFIGURATION =====
# Customize these colors for bet-worthy race highlighting

# Background color for bet-worthy races (light yellow/gold)
BET_WORTHY_FILL_COLOR = "FFFF99"  # Light yellow

# Font color for bet-worthy races (keep black for readability)
BET_WORTHY_FONT_COLOR = "000000"  # Black

# Header background color
HEADER_FILL_COLOR = "4472C4"  # Blue

# Header font color
HEADER_FONT_COLOR = "FFFFFF"  # White


def export_to_excel_with_formatting(df, bet_worthy_races, output_path):
    """
    Export DataFrame to Excel with conditional formatting for bet-worthy races.
    
    Args:
        df: DataFrame with race data
        bet_worthy_races: Dict from bet_worthy.identify_bet_worthy_races()
                          Maps (Track, RaceNumber) -> {'worthy': bool, ...}
        output_path: Full path where Excel file should be saved
    """
    print(f"\n📊 Creating Excel file with conditional formatting...")
    
    # Create a new workbook and select active sheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Race Analysis"
    
    # Define styles
    bet_worthy_fill = PatternFill(start_color=BET_WORTHY_FILL_COLOR,
                                   end_color=BET_WORTHY_FILL_COLOR,
                                   fill_type="solid")
    
    header_fill = PatternFill(start_color=HEADER_FILL_COLOR,
                               end_color=HEADER_FILL_COLOR,
                               fill_type="solid")
    
    header_font = Font(bold=True, color=HEADER_FONT_COLOR)
    bet_worthy_font = Font(color=BET_WORTHY_FONT_COLOR)
    
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Write headers
    headers = list(df.columns)
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Track statistics
    total_rows = 0
    highlighted_rows = 0
    
    # Write data rows
    for row_idx, (_, row_data) in enumerate(df.iterrows(), start=2):
        track = row_data.get('Track', '')
        race_num = row_data.get('RaceNumber', 0)
        
        # Check if this race is bet-worthy
        race_key = (track, race_num)
        is_bet_worthy = bet_worthy_races.get(race_key, {}).get('worthy', False)
        
        if is_bet_worthy:
            highlighted_rows += 1
        
        # Write each cell in the row
        for col_idx, (col_name, value) in enumerate(row_data.items(), start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = border
            
            # Apply formatting only to bet-worthy races
            if is_bet_worthy:
                cell.fill = bet_worthy_fill
                cell.font = bet_worthy_font
        
        total_rows += 1
    
    # Auto-adjust column widths (basic approach)
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        
        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except (TypeError, AttributeError) as e:
                # Skip cells that can't be converted to string
                pass
        
        adjusted_width = min(max_length + 2, 50)  # Cap at 50 for very long values
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Freeze the header row
    ws.freeze_panes = 'A2'
    
    # Save the workbook
    wb.save(output_path)
    
    print(f"✅ Excel file saved: {output_path}")
    print(f"   Total rows: {total_rows}")
    print(f"   Highlighted (bet-worthy) rows: {highlighted_rows}")
    print(f"   Non-highlighted rows: {total_rows - highlighted_rows}")
    
    return output_path


def export_simple_excel(df, output_path):
    """
    Export DataFrame to Excel without any special formatting (fallback method).
    
    Args:
        df: DataFrame to export
        output_path: Full path where Excel file should be saved
    """
    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"✅ Excel file saved (no formatting): {output_path}")
    return output_path

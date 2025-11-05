# GREYHOUND COMPLETE ANALYZER - FIXED EXCEL EXPORT
import os
import sys
import pdfplumber
import re
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

class GreyhoundFormParser:
    def __init__(self):
        self.dog_count = 0
    
    def parse_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Parse PDF with CORRECTED date and name extraction"""
        dogs = []
        
        print(f"PARSING {os.path.basename(pdf_path)}...")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract text from all pages
                full_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                
                if not full_text:
                    return dogs
                
                # Show first 10 lines for debugging
                lines = full_text.split('\n')
                print("   First 10 lines for debugging:")
                for i, line in enumerate(lines[:10], 1):
                    print(f"      {i}: {line}")
                
                # Extract race info and dogs
                race_info = self._extract_race_info_corrected(full_text, pdf_path)
                page_dogs = self._extract_dogs_corrected_names(full_text, race_info)
                dogs.extend(page_dogs)
                
                print(f"Found {len(page_dogs)} dogs")
        
        except Exception as e:
            print(f"ERROR parsing {pdf_path}: {e}")
        
        return dogs
    
    def _extract_race_info_corrected(self, text: str, pdf_path: str) -> Dict[str, Any]:
        """Extract race information with CORRECTED date as race number"""
        race_info = {
            'track_name': 'Unknown',
            'distance': 'Unknown', 
            'race_time': 'Unknown',
            'race_date': 'Unknown',
            'race_number': '1',  # Will be replaced with date
            'source_file': os.path.basename(pdf_path)
        }
        
        try:
            # Extract track name, date, and distance from "Race No 16 Oct 25 06:37PM Angle Park 530m"
            track_match = re.search(r'Race\s+No\s+(\d+\s+[A-Za-z]+\s+\d+)\s+(\d+:\d+[AP]M)\s+([A-Z\s]+?)\s+(\d+m)', text)
            if track_match:
                race_info['race_date'] = track_match.group(1)  # "16 Oct 25"
                race_info['race_time'] = track_match.group(2)  # "06:37PM"
                race_info['track_name'] = track_match.group(3).strip()  # "Angle Park"
                race_info['distance'] = track_match.group(4)  # "530m"
                
                # Use date as race number since that's what appears in the PDF
                race_info['race_number'] = race_info['race_date']
                print(f"   FOUND: {race_info['track_name']} Race {race_info['race_number']} - Date: {race_info['race_date']}")
            else:
                # Fallback pattern
                fallback_match = re.search(r'Race\s+No\s+(\d+\s+[A-Za-z]+\s+\d+)', text)
                if fallback_match:
                    race_info['race_date'] = fallback_match.group(1)
                    race_info['race_number'] = race_info['race_date']
                    print(f"   Found fallback race: {race_info['race_number']}")
            
        except Exception as e:
            print(f"WARNING: Error extracting race info: {e}")
        
        return race_info
    
    def _extract_dogs_corrected_names(self, text: str, race_info: Dict) -> List[Dict[str, Any]]:
        """Extract dogs with CORRECTED name parsing"""
        dogs = []
        
        # IMPROVED PATTERN: Better name extraction to avoid cutting off names
        pattern = r'(\d+)\.\s+([a-zA-Z]?\d*[a-zA-Z]*)\s*([A-Z][A-Za-z\s\']+(?=\s+\d+[db]|\s*$))'
        
        matches = re.findall(pattern, text)
        
        for match in matches:
            try:
                list_order = int(match[0])
                form_code = match[1] if match[1] else "Unknown"
                dog_name = match[2].strip()
                
                # Now extract the rest of the data using the full name
                full_pattern = rf'{re.escape(dog_name)}\s+(\d+[db])\s+([\d.]+kg)\s+(\d+)\s+([A-Za-z\s]+?)\s+(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\s+\$([\d,]+)'
                detail_match = re.search(full_pattern, text)
                
                if detail_match:
                    age_sex = detail_match.group(1)
                    weight = detail_match.group(2)
                    box_num = int(detail_match.group(3))
                    trainer = detail_match.group(4).strip()
                    wins = int(detail_match.group(5))
                    places = int(detail_match.group(6))
                    starts = int(detail_match.group(7))
                    prize_money = f"${detail_match.group(8)}"
                    
                    # Enhanced data analysis
                    recent_form = self._analyze_form_code(form_code)
                    career_stats = self._calculate_career_metrics(wins, places, starts)
                    
                    dog_data = {
                        # Race context - USING DATE AS RACE NUMBER
                        'Track': race_info['track_name'],
                        'Race': race_info['race_number'],  # Date as race number
                        'Box': box_num,
                        'DogsName': dog_name,  # FULL name
                        'form_code': form_code,
                        
                        # Core performance data
                        'wins': wins,
                        'places': places,
                        'starts': starts,
                        'PrizeMoney': prize_money,
                        
                        # Race date information
                        'Date': race_info['race_date'],
                        'race_time': race_info['race_time'],
                        'distance': race_info['distance'],
                        
                        # Physical attributes
                        'age_sex': age_sex,
                        'trainer': trainer,
                        
                        # Enhanced metrics
                        'recent_races': recent_form['recent_races'],
                        'recent_positions': str(recent_form['recent_positions']),
                        'avg_recent_position': recent_form['avg_recent_position'],
                        'best_recent_position': recent_form['best_recent_position'],
                        'worst_recent_position': recent_form['worst_recent_position'],
                        'form_trend': recent_form['form_trend'],
                        'has_win': recent_form['has_win'],
                        'has_place': recent_form['has_place'],
                        'has_dnf': recent_form['has_dnf'],
                        'consistent_places': recent_form['consistent_places'],
                        
                        # Career metrics
                        'win_percentage': career_stats['win_percentage'],
                        'place_percentage': career_stats['place_percentage'],
                        'strike_rate': career_stats['strike_rate'],
                        'consistency_rate': career_stats['consistency_rate'],
                        'experience_level': career_stats['experience_level'],
                        
                        # Source
                        'source_file': race_info['source_file']
                    }
                    
                    dogs.append(dog_data)
                    self.dog_count += 1
                    
                    # Show dogs with FULL names
                    print(f"   OK {race_info['track_name']} Race {race_info['race_number']} Box {box_num}: {dog_name}")
                    
                else:
                    print(f"   WARNING: Could not extract details for: {dog_name}")
                
            except Exception as e:
                print(f"   WARNING: Error parsing dog: {e}")
                continue
        
        return dogs
    
    def _analyze_form_code(self, form_code: str) -> Dict[str, Any]:
        """Analyze form code to extract recent performance patterns"""
        if form_code == "Unknown":
            return {
                'recent_races': 0,
                'recent_positions': [],
                'avg_recent_position': 8.0,
                'best_recent_position': 8,
                'worst_recent_position': 8,
                'form_trend': 0,
                'has_win': False,
                'has_place': False,
                'has_dnf': False,
                'consistent_places': 0
            }
        
        recent_positions = []
        form_quality_indicators = {
            'has_win': False,
            'has_place': False,
            'has_dnf': False,
            'consistent_places': 0
        }
        
        for char in form_code:
            if char.isdigit():
                position = int(char)
                recent_positions.append(position)
                if position == 1:
                    form_quality_indicators['has_win'] = True
                if position <= 3:
                    form_quality_indicators['has_place'] = True
            elif char.lower() == 'x':
                recent_positions.append(8)
                form_quality_indicators['has_dnf'] = True
            elif char.lower() == 'f':
                recent_positions.append(7)
                form_quality_indicators['has_dnf'] = True
        
        # Calculate form metrics
        if recent_positions:
            avg_position = sum(recent_positions) / len(recent_positions)
            best_recent = min(recent_positions)
            worst_recent = max(recent_positions)
            form_trend = self._calculate_form_trend(recent_positions)
            consistent_places = sum(1 for pos in recent_positions if pos <= 3)
            form_quality_indicators['consistent_places'] = consistent_places
        else:
            avg_position = 8.0
            best_recent = 8
            worst_recent = 8
            form_trend = 0
            form_quality_indicators['consistent_places'] = 0
        
        return {
            'recent_races': len(recent_positions),
            'recent_positions': recent_positions,
            'avg_recent_position': round(avg_position, 2),
            'best_recent_position': best_recent,
            'worst_recent_position': worst_recent,
            'form_trend': form_trend,
            'has_win': form_quality_indicators['has_win'],
            'has_place': form_quality_indicators['has_place'],
            'has_dnf': form_quality_indicators['has_dnf'],
            'consistent_places': form_quality_indicators['consistent_places']
        }
    
    def _calculate_form_trend(self, positions: List[int]) -> float:
        """Calculate if form is improving or declining"""
        if len(positions) < 2:
            return 0
        
        x = list(range(len(positions)))
        y = positions
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            return round(slope, 3)
        except:
            return 0
    
    def _calculate_career_metrics(self, wins: int, places: int, starts: int) -> Dict[str, Any]:
        """Calculate enhanced career metrics"""
        if starts == 0:
            return {
                'win_percentage': 0.0,
                'place_percentage': 0.0,
                'strike_rate': 0.0,
                'consistency_rate': 0.0,
                'experience_level': 'Novice'
            }
        
        win_pct = (wins / starts) * 100
        place_pct = ((wins + places) / starts) * 100
        
        # Experience level
        if starts >= 30:
            experience_level = 'Veteran'
        elif starts >= 15:
            experience_level = 'Experienced'
        elif starts >= 5:
            experience_level = 'Developing'
        else:
            experience_level = 'Novice'
        
        return {
            'win_percentage': round(win_pct, 2),
            'place_percentage': round(place_pct, 2),
            'strike_rate': round(win_pct, 2),
            'consistency_rate': round(place_pct, 2),
            'experience_level': experience_level
        }

# Setup directories
BASE_DIR = os.path.dirname(current_dir)
PDF_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')

def setup_environment():
    """Setup and validate environment"""
    print("SETTING UP ENVIRONMENT...")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"CREATED outputs directory: {OUTPUT_DIR}")
    else:
        print(f"OUTPUTS directory exists: {OUTPUT_DIR}")
    
    return True

def find_pdf_files():
    """Find all PDF files in data directory"""
    if os.path.exists(PDF_DIR):
        pdf_files = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
        if pdf_files:
            print(f"FOUND {len(pdf_files)} PDF files")
            return pdf_files
        else:
            print("ERROR: No PDF files found in data folder!")
    else:
        print("ERROR: Data folder not found!")
    
    return []

def generate_enhanced_score(dog_data: Dict) -> float:
    """Generate enhanced score using all available data"""
    try:
        base_score = 50.0
        
        # 1. CAREER PERFORMANCE (35 points max)
        if dog_data['starts'] > 0:
            # Win percentage (0-15 points)
            win_rate = dog_data['win_percentage'] / 100
            base_score += win_rate * 15
            
            # Consistency (0-10 points)
            consistency_rate = dog_data['consistency_rate'] / 100
            base_score += consistency_rate * 10
            
            # Experience bonus (0-10 points)
            if dog_data['experience_level'] == 'Veteran':
                base_score += 8
            elif dog_data['experience_level'] == 'Experienced':
                base_score += 6
            elif dog_data['experience_level'] == 'Developing':
                base_score += 3
        
        # 2. RECENT FORM (30 points max)
        if dog_data['recent_races'] > 0:
            # Recent average position (0-15 points)
            position_score = max(0, 15 - (dog_data['avg_recent_position'] * 2))
            base_score += position_score
            
            # Form trend (0-8 points)
            trend_bonus = max(0, 8 + (dog_data['form_trend'] * -20))
            base_score += trend_bonus
            
            # Recent wins/places (0-7 points)
            if dog_data['has_win']:
                base_score += 4
            if dog_data['has_place']:
                base_score += 2
            if dog_data['consistent_places'] >= 2:
                base_score += min(3, dog_data['consistent_places'])
        
        # 3. RACE CONTEXT (20 points max)
        # Box position (0-5 points) - boxes 1-4 generally preferred
        if dog_data['Box'] <= 4:
            base_score += 3
        elif dog_data['Box'] <= 6:
            base_score += 1
        
        # Prize money performance (0-10 points)
        try:
            money_value = float(dog_data['PrizeMoney'].replace('$', '').replace(',', ''))
            money_per_start = money_value / max(1, dog_data['starts'])
            money_bonus = min(10, money_per_start / 200)
            base_score += money_bonus
        except:
            pass
        
        # 4. PENALTIES (up to -15 points)
        if dog_data['has_dnf']:
            base_score -= 5
        if dog_data['avg_recent_position'] > 6:
            base_score -= 5
        if dog_data['experience_level'] == 'Novice':
            base_score -= 3
        
        return min(100.0, max(0.0, round(base_score, 1)))
        
    except Exception as e:
        print(f"WARNING: Scoring error for {dog_data.get('DogsName', 'Unknown')}: {e}")
        return 50.0

def calculate_bet_recommendation(race_dogs: pd.DataFrame) -> pd.DataFrame:
    """Calculate betting recommendations - ONLY ONE WINNER PER RACE with tie-breakers"""
    if len(race_dogs) == 0:
        return race_dogs
    
    # Reset index to ensure proper sorting
    race_dogs = race_dogs.reset_index(drop=True)
    
    # Find all dogs with the maximum score
    max_score = race_dogs['FinalScore'].max()
    top_dogs = race_dogs[race_dogs['FinalScore'] == max_score]
    
    # If multiple dogs have the same top score, use tie-breakers
    if len(top_dogs) > 1:
        print(f"   TIE DETECTED: {len(top_dogs)} dogs with score {max_score}")
        
        # Tie-breaker 1: Best recent form (lowest avg recent position)
        best_recent = top_dogs['avg_recent_position'].min()
        top_dogs = top_dogs[top_dogs['avg_recent_position'] == best_recent]
        
        # Tie-breaker 2: Most consistent (highest consistency rate)
        if len(top_dogs) > 1:
            best_consistency = top_dogs['consistency_rate'].max()
            top_dogs = top_dogs[top_dogs['consistency_rate'] == best_consistency]
        
        # Tie-breaker 3: Most experienced (prefer veterans)
        if len(top_dogs) > 1:
            experience_order = ['Veteran', 'Experienced', 'Developing', 'Novice']
            for exp_level in experience_order:
                experienced_dogs = top_dogs[top_dogs['experience_level'] == exp_level]
                if len(experienced_dogs) > 0:
                    top_dogs = experienced_dogs
                    break
        
        # Final tie-breaker: Best box position (lower is better)
        if len(top_dogs) > 1:
            best_box = top_dogs['Box'].min()
            top_dogs = top_dogs[top_dogs['Box'] == best_box]
    
    # Select the single winner (take first if still tied after all breakers)
    top_dog_index = top_dogs.index[0]
    top_score = race_dogs.loc[top_dog_index, 'FinalScore']
    
    # Initialize all as PASS
    race_dogs['Bet'] = 'PASS'
    
    # Assign YES to ONLY the top dog
    race_dogs.loc[top_dog_index, 'Bet'] = 'YES'
    print(f"   WINNER: {race_dogs.loc[top_dog_index, 'DogsName']} (Score: {top_score}, Box: {race_dogs.loc[top_dog_index, 'Box']})")
    
    # Assign PLACE to dogs within 3 points of top score (excluding the YES dog)
    place_count = 0
    for idx, row in race_dogs.iterrows():
        if idx != top_dog_index:  # Don't change the YES dog
            score_gap = top_score - row['FinalScore']
            if score_gap <= 3:
                race_dogs.loc[idx, 'Bet'] = 'PLACE'
                place_count += 1
    
    if place_count > 0:
        print(f"   PLACE BETS: {place_count} dogs within 3 points")
    
    return race_dogs

def analyze_dogs(dogs: List[Dict]) -> pd.DataFrame:
    """Analyze dogs with enhanced metrics and betting recommendations"""
    if not dogs:
        return pd.DataFrame()
    
    df = pd.DataFrame(dogs)
    
    print("CALCULATING ENHANCED SCORES...")
    df['FinalScore'] = df.apply(generate_enhanced_score, axis=1)
    
    df['KmH'] = df.apply(
        lambda x: min(100, max(40, x['FinalScore'] + (x['win_percentage'] * 0.1))), 
        axis=1
    )
    
    print("CALCULATING BETTING RECOMMENDATIONS...")
    grouped_dfs = []
    
    # Group by Track AND Race (date)
    for (track_name, race_number), race_group in df.groupby(['Track', 'Race']):
        print(f"   PROCESSING {track_name} Race {race_number} ({len(race_group)} dogs)...")
        race_with_bets = calculate_bet_recommendation(race_group)
        grouped_dfs.append(race_with_bets)
    
    if grouped_dfs:
        df = pd.concat(grouped_dfs, ignore_index=True)
    
    # Sort by Track, Race (date), and Box number
    df = df.sort_values(['Track', 'Race', 'Box'], ascending=[True, True, True])
    
    return df

def save_final_results(df, output_dir):
    """Save final results with CORRECTED data - FIXED EXCEL EXPORT"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define column order - use the EXACT column names that exist in the DataFrame
    primary_columns = [
        'Track', 'Race', 'Box', 'DogsName', 'Bet', 
        'FinalScore', 'PrizeMoney', 'KmH'
    ]
    
    # Get all columns that actually exist in the DataFrame
    available_columns = df.columns.tolist()
    
    # Separate primary columns that exist from others
    existing_primary_columns = [col for col in primary_columns if col in available_columns]
    other_columns = [col for col in available_columns if col not in existing_primary_columns]
    
    # Ensure Date is at the end if it exists
    if 'Date' in other_columns:
        other_columns.remove('Date')
        other_columns.append('Date')
    
    # Create final column order
    final_column_order = existing_primary_columns + other_columns
    
    # Create final DataFrame with the correct column order
    final_df = df[final_column_order].copy()
    
    excel_file = os.path.join(output_dir, f'greyhound_fixed_analysis_{timestamp}.xlsx')
    
    try:
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            final_df.to_excel(writer, sheet_name='Complete Analysis', index=False)
            
            # Create summary using the CORRECT column names that exist in the DataFrame
            summary_data = {
                'Metric': [
                    'Total Dogs', 'Total Races', 'YES Recommendations',
                    'PLACE Recommendations', 'Average Final Score', 'Analysis Date'
                ],
                'Value': [
                    len(df),
                    df[['Track', 'Race']].drop_duplicates().shape[0],
                    len(df[df['Bet'] == 'YES']),
                    len(df[df['Bet'] == 'PLACE']),
                    f"{df['FinalScore'].mean():.1f}",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        print(f"EXCEL FILE SAVED: {excel_file}")
        print(f"PRIMARY COLUMNS: {', '.join(existing_primary_columns)}")
        print(f"ADDITIONAL VARIABLES: {len(other_columns)} columns")
        print(f"TOTAL COLUMNS IN SPREADSHEET: {len(final_df.columns)}")
        
        return {'excel': excel_file}
        
    except Exception as e:
        print(f"ERROR SAVING EXCEL FILE: {e}")
        return {}

def main():
    """Main execution function"""
    print("GREYHOUND COMPLETE ANALYZER - FIXED EXCEL EXPORT")
    print("=" * 60)
    print("FIXED: Excel column naming and export")
    print("FIXED: Only ONE YES bet per race") 
    print("ALL VARIABLES in spreadsheet")
    print("=" * 60)
    
    setup_environment()
    pdf_files = find_pdf_files()
    if not pdf_files:
        return
    
    parser = GreyhoundFormParser()
    all_dogs = []
    
    print(f"PROCESSING PDF FILES...")
    print("-" * 50)
    
    for pdf_file in pdf_files:
        dogs = parser.parse_pdf(pdf_file)
        all_dogs.extend(dogs)
        print(f"{os.path.basename(pdf_file)}: {len(dogs)} dogs extracted")
    
    if not all_dogs:
        print("ERROR: No dogs could be extracted from the PDF files!")
        return
    
    print(f"ANALYZING {len(all_dogs)} DOGS...")
    df = analyze_dogs(all_dogs)
    
    print(f"ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"Total dogs analyzed: {len(df)}")
    print(f"Final score range: {df['FinalScore'].min():.1f} - {df['FinalScore'].max():.1f}")
    print(f"Average final score: {df['FinalScore'].mean():.1f}")
    
    # Show race distribution
    race_counts = df.groupby(['Track', 'Race']).size().reset_index()
    race_counts.columns = ['Track', 'Race', 'Dogs']
    print(f"Unique races: {len(race_counts)}")
    print("RACE DISTRIBUTION:")
    print("-" * 30)
    for _, race in race_counts.iterrows():
        print(f"   {race['Track']}_Race_{race['Race']}: {race['Dogs']} dogs")
    
    # Betting summary - NOW WITH ONLY ONE YES PER RACE
    yes_count = len(df[df['Bet'] == 'YES'])
    place_count = len(df[df['Bet'] == 'PLACE'])
    pass_count = len(df[df['Bet'] == 'PASS'])
    
    print("BETTING RECOMMENDATIONS")
    print("=" * 60)
    print(f"YES (Win bets): {yes_count} dogs - ONE PER RACE")
    print(f"PLACE (Place bets): {place_count} dogs")
    print(f"PASS (Avoid): {pass_count} dogs")
    
    # Verify we have exactly one YES per race
    race_bet_counts = df.groupby(['Track', 'Race'])['Bet'].apply(
        lambda x: (x == 'YES').sum()
    ).reset_index()
    
    multiple_winners = race_bet_counts[race_bet_counts['Bet'] > 1]
    if len(multiple_winners) > 0:
        print(f"ERROR: {len(multiple_winners)} races have multiple YES bets!")
    else:
        print(f"SUCCESS: Exactly one YES bet per race!")
    
    # Save results
    output_files = save_final_results(df, OUTPUT_DIR)
    
    print(f"COMPLETE ANALYSIS SUCCESSFULLY COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    main()
import io
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from bot.models.survey import Question

# Set plot style
plt.style.use('ggplot')

def generate_excel_report(records: List[Dict[str, Any]]) -> io.BytesIO:
    """Generate an Excel file from registration records with Detailed and Summarized sheets."""
    df = pd.DataFrame(records)
    
    if not df.empty:
        # Normalize old Amharic data to English keys
        from bot.survey_config import TRANSPORT_SURVEY
        from bot.translations import TRANSLATIONS
        am_options = TRANSLATIONS.get("am", {})
        for q in TRANSPORT_SURVEY.questions:
            if isinstance(q.options, list) and q.id in df.columns:
                inverse_options = {}
                for opt in q.options:
                    am_val = am_options.get(f"opt_{opt}")
                    if am_val:
                        inverse_options[am_val] = opt
                df[q.id] = df[q.id].replace(inverse_options)

        summary_cols_mapping = {
            "full_name": "Full Name",
            "telegram_user_id": "Telegram User ID",
            "contact_phone": "Phone Number",
            "block_number": "Block Number",
            "house_number": "House Number",
            "destination": "Destination",
            "morning_departure_time": "Morning Time",
            "evening_pickup_time": "Evening Time",
            "service_frequency": "Service Frequency",
            "telegram_username": "Username"
        }
        cols_to_keep = [c for c in summary_cols_mapping.keys() if c in df.columns]
        df_summary = df[cols_to_keep].rename(columns=summary_cols_mapping)
        # Also rename columns in the detailed sheet for consistency
        df = df.rename(columns=summary_cols_mapping)
    else:
        df_summary = pd.DataFrame()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Detailed')
        df_summary.to_excel(writer, index=False, sheet_name='Summarized')

    output.seek(0)
    return output

def generate_visual_summary(records: List[Dict[str, Any]], questions: List[Question]) -> List[io.BytesIO]:
    """Generate bar charts for choice questions."""
    df = pd.DataFrame(records)
    images = []
    
    if df.empty:
        return images
        
    # Filter for choice questions that actually have data
    choice_qs = [q for q in questions if q.type == "choice" and q.id in df.columns]
    
    for q in choice_qs:
        plt.figure(figsize=(10, 6))
        
        # Normalize old Amharic data to English keys if options is a list
        if isinstance(q.options, list):
            from bot.translations import TRANSLATIONS, t
            am_options = TRANSLATIONS.get("am", {})
            inverse_options = {}
            for opt in q.options:
                am_val = am_options.get(f"opt_{opt}")
                if am_val:
                    inverse_options[am_val] = opt
            df[q.id] = df[q.id].replace(inverse_options)
            
        counts = df[q.id].value_counts()
        
        # Create bar plot
        ax = counts.plot(kind='bar', color='skyblue', edgecolor='navy')
        plt.title(f"Breakdown: {t(q.label, 'en')}", fontsize=14, pad=20)
        plt.xlabel(t(q.label, 'en'), fontsize=12)
        plt.ylabel("Number of Residents", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Add value labels on top of bars
        for i, v in enumerate(counts):
            ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')

        # Save plot to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        buf.seek(0)
        images.append(buf)
        plt.close()
        
    return images

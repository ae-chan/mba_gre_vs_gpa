import pandas as pd
import os
import re
import logging
from datetime import datetime

logging.basicConfig(
    filename='clear_admit_parser.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, '%B %d, %Y %I:%M%p').strftime('%Y-%m-%d')
    except ValueError:
        try:
            return datetime.strptime(date_string, '%B %d, %Y').strftime('%Y-%m-%d')
        except ValueError:
            logging.error(f"Unable to parse date: {date_string}")
            return None

def parse_entry(entry):
    try:
        data = {}
        lines = entry.strip().split('\n')
        first_line = lines[0].split(' ')

        date_string = ' '.join(first_line[:3])
        data['Date'] = parse_date(date_string)

        school_match = re.search(r'Accepted (?:from Waitlist )?to (.+)', lines[1])
        data['School'] = school_match.group(1) if school_match else ''
        data['Waitlist'] = 'Yes' if 'from Waitlist' in lines[1] else 'No'

        for line in lines[2:]:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        data['GPA'] = data.get('GPA', '')
        data['GRE'] = data.get('GRE', '')
        data['Post-MBA Career'] = data.get('Post MBA Career Name', '')
        return data

    except Exception as e:
        logging.error(f"Error parsing entry: {str(e)}")
        return None

def parse_webpage(content):
    entries = content.split('Notify me')
    parsed_data = [parse_entry(entry) for entry in entries if entry.strip()]
    return [entry for entry in parsed_data if entry is not None]

def parse_clear_admit(input_filename, output_filename):
    try:
        with open(input_filename, 'r', encoding='utf-8') as file:
            content = file.read()
        parsed_data = parse_webpage(content)
        df = pd.DataFrame(parsed_data)
        
        columns = [
            'School',
            'GPA',
            'GRE',
            'Program Type',
            'Application Location',
            'Date',
            'Round',
            'Post-MBA Career', 
            'Note']
        df = df.reindex(columns=columns)

        df['GPA'] = pd.to_numeric(df['GPA'], errors='coerce')
        df['GRE'] = pd.to_numeric(df['GRE'], errors='coerce')
        df = df.dropna(subset=['GPA', 'GRE'])
        
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        df.to_csv(output_filename, index=False)
        logging.info(f"CSV file '{output_filename}' has been created successfully.")
        return df
    
    except FileNotFoundError:
        logging.error(f"Input file not found at '{input_filename}'")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    
    return None

if __name__ == "__main__":
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        mba_folder_path = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        input_filename = os.path.join(mba_folder_path, 'research', 'data', 'raw', 'clear_admit.txt')
        output_filename = os.path.join(mba_folder_path, 'research', 'data', 'intermediate', 'clear_admit_parsed.csv')
        
        df = parse_clear_admit(input_filename, output_filename)
        if df is not None:
            print(df.head())
        else:
            print("Failed to parse the data. Check the log file for details.")
    
    except Exception as e:
        logging.critical(f"Critical error in main execution: {str(e)}")
        print(f"A critical error occurred. Check the log file for details.")

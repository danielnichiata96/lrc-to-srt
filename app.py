from flask import Flask, request, send_file, render_template_string
import os
import re

app = Flask(__name__)

def replace_notes(text):
    # Replace ♪ with ♫ in the text
    return text.replace('♪', '♫')

def censor_text(text):
    curse_words = {
        'ass': 'a**',
        'bitch': 'b****',
        'bitches': 'b******',
        'boob': 'b***',
        'boobs': 'b****',
        'butt': 'b***',
        'booty': 'b****',
        'bullshit': 'bulls****',
        'bloodcaat': 'b********',
        'cock': 'c***',
        'clit': 'c***',
        'cum': 'c**',
        'damn': 'd***',
        'dick': 'd***',
        'faggot': 'f*****',
        'fode': 'f***',
        'fodendo': 'f******',
        'fuder': 'f****',
        'fuck': 'f***',
        'fucker': 'f*****',
        'fuckin': 'f*****',
        'fucked': 'f*****',
        'nut': 'n**',
        'nuts': 'n***',
        'motherfuckin': 'motherf*****',
        'motherfucking': 'motherf******',
        'motherfuckers': 'motherf******',
        'motherfucker': 'motherf*****',
        'semen': 's****',
        'shit': 's***',
        'shits': 's****',
        'shitty': 's****',
        'shittin': 's******',
        'suckin': 's*****',
        'twat': 't***',
        'thot': 't***',
        'tit': 't**',
        'tits': 't***',
        'nigga': 'n****',
        'niggas': 'n*****',
        'pussy': 'p****',
        'hoe': 'h**',
        'hoes': 'h***',
        'gangbang': 'g*******',
        'jizz': 'j***',
        'pau': 'p**',
        'xota': 'x***',
        'xoxota': 'x*****',
        'vagina': 'v*****',
        'mierda': 'm*****',
        'bellacona': 'b********',
        'cabrón': 'c*****',
        'cojone': 'c*****',
        'carajo': 'c*****',
        'culo': 'c***',
        'chinga': 'c*****',
        'chingué': 'c******',
        'chingar': 'c******',
        'chingamo': 'c*******',
        'teta': 't***',
        'pendejo': 'p******',
        'piranha': 'p******',
        'puta': 'p***',
        'puñeta': 'p*****',
        'jodió': 'j****',
        'folla': 'f****',
        'verga': 'v****',
        'bloodclaat': 'b*********',
        'rassclaat': 'r********',

    }
    # Words that are substrings of other words and should not match inside other words
    substring_sensitive = {'ass', 'nut', 'tit', 'cum', 'damn', 'hoe', 'pau', 'verga', 'puta', 'mierda', 'teta', 'culo', 'clit', 'cock'}
    for word, censored_word in curse_words.items():
        if word in substring_sensitive:
            # Use negative lookbehind and lookahead to avoid matching inside other words
            pattern = rf'(?<!\w){word}(?!\w)'
        else:
            # Use word boundaries for other words
            pattern = rf'\b{word}\b'
        text = re.sub(pattern, censored_word, text, flags=re.IGNORECASE)
    return text

def selective_normalize(text):
    # Replace only specific characters
    replacements = {
        'ṣ': 's',
        'ẹ': 'e',
        'ạ': 'a',
        'ọ': 'o'  # Added this line
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text

def lrc_to_srt(lrc_content):
    subs = []
    pattern = r'\[(\d+:\d+\.\d+)\](.*)'
    matches = re.findall(pattern, lrc_content)
    
    for idx, match in enumerate(matches):
        timestamp, text = match
        
        # Process text to replace notes, censor, and selectively normalize
        if not text.strip():
            text = '♫'
        else:
            text = selective_normalize(censor_text(replace_notes(text)))
        
        # Start and end times based on exact LRC timestamps
        start_time = timestamp
        end_time = matches[idx + 1][0] if idx + 1 < len(matches) else None
        
        subs.append(f"{len(subs) + 1}\n{format_srt_timestamp(start_time)} --> {format_srt_timestamp(end_time)}\n{text.strip()}\n")

    # Remove last entry if it's an instrumental break (♫) at the end
    if subs and "♫" in subs[-1]:
        subs.pop()

    return '\n'.join(subs)

def format_srt_timestamp(timestamp):
    # Converts LRC-style timestamps (e.g., '01:23.45') to SRT format (e.g., '00:01:23,450')
    if timestamp is None:
        return None  # Last subtitle may not have an end time
    minutes, seconds = timestamp.split(':')
    seconds, milliseconds = seconds.split('.')
    return f"00:{minutes.zfill(2)}:{seconds.zfill(2)},{milliseconds.ljust(3, '0')}"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part", 400
        file = request.files['file']
        if file.filename == '' or not file.filename.endswith('.lrc'):
            return "No selected file or file type is not .lrc", 400
        
        lrc_content = file.read().decode('utf-8')
        srt_content = lrc_to_srt(lrc_content)
        
        srt_file_path = os.path.join("temp.srt")
        with open(srt_file_path, 'w', encoding='utf-8') as srt_file:
            srt_file.write(srt_content)
        
        return send_file(srt_file_path, as_attachment=True, download_name=file.filename.replace('.lrc', '.srt'))

    # Simple HTML form to upload the file
    html_form = '''
    <!doctype html>
    <title>Upload LRC File</title>
    <h1>Upload an .lrc file to convert to .srt</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Convert>
    </form>
    '''
    return render_template_string(html_form)

if __name__ == "__main__":
    app.run(debug=True)

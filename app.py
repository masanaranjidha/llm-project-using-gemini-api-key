from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import sys
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import tempfile
import google.generativeai as genai
from debug_config import (
    DEBUG_CONFIG, 
    start_performance_tracking, 
    end_performance_tracking, 
    is_debug_enabled,
    setup_logging
)

# Initialize logging with rotation
logger = setup_logging()

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# In-memory storage
current_data = {
    'df': None,
    'chat_history': []
}

# Configure Gemini
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-pro')
    logger.info("Gemini API initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini API: {str(e)}")
    raise


def log_error(e: Exception, context: str = ""):
    """Utility function to log errors with full traceback"""
    error_msg = f"{context} - Error: {str(e)}\nTraceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
    logger.error(error_msg)
    return error_msg

def process_query(df, query, chat_history=[]):
    start_time = start_performance_tracking()
    try:
        logger.info(f"Processing query: {query}")
        if is_debug_enabled('QUERIES'):
            logger.debug(f"DataFrame shape: {df.shape}")
            logger.debug(f"Chat history length: {len(chat_history)}")
        
        # Prepare the context with DataFrame information
        context = f"""DataFrame Info:
Rows: {df.shape[0]}
Columns: {df.columns.tolist()}
Sample data (first 5 rows):
{df.head().to_string()}

Data Types:
{df.dtypes.to_string()}"""
        
        # Include chat history in the prompt
        history_text = ""
        if chat_history:
            history_text = "### Previous Conversation:\n" + "\n".join([f"Q: {h['user']}\nA: {h['assistant']}" for h in chat_history[-3:]])
            history_text += "\n\n"
            logger.debug(f"Including chat history: {history_text}")

        # Create the complete prompt
        prompt = f"""{history_text}Based on this DataFrame:
{context}

User Question: {query}

Please provide a clear and data-driven answer. Include specific numbers and calculations when relevant."""

        logger.debug("Sending request to Gemini API")
        # Get response from Gemini
        response = model.generate_content(prompt)
        logger.info("Successfully received response from Gemini")
        logger.debug(f"Gemini response: {response.text[:200]}...")  # Log first 200 chars of response
        
        return response.text
    except Exception as e:
        error_msg = log_error(e, "Error in process_query")
        return f"Error processing query: {str(e)}"
    finally:
        if start_time:
            processing_time = end_performance_tracking(start_time)
            logger.debug(f"Query processing time: {processing_time:.2f} seconds")

@app.route('/')
def index():
    try:
        logger.info("Rendering index page")
        return render_template('index.html')
    except Exception as e:
        log_error(e, "Error rendering index page")
        return "Internal Server Error", 500

@app.route('/upload', methods=['POST'])
def upload_file():
    start_time = start_performance_tracking()
    try:
        logger.info("File upload initiated")
        
        if 'file' not in request.files:
            logger.warning("No file part in request")
            return jsonify({'error': 'No file part'})
        
        file = request.files['file']
        if file.filename == '':
            logger.warning("No selected file")
            return jsonify({'error': 'No selected file'})
        
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                file.save(filepath)
                logger.debug(f"Reading CSV file: {filename}")
                df = pd.read_csv(filepath)
                logger.info(f"Successfully read CSV with shape: {df.shape}")
                
                preview = df.head().to_html(classes='table table-striped table-hover')
                stats = {
                    'rows': df.shape[0],
                    'columns': df.shape[1],
                    'columns_list': df.columns.tolist()
                }
                
                # Store in memory
                current_data['df'] = df
                current_data['chat_history'] = []
                
                return jsonify({
                    'success': True,
                    'preview': preview,
                    'stats': stats
                })
            except Exception as e:
                error_msg = log_error(e, f"Error processing CSV file: {filename}")
                return jsonify({'error': f'Error processing CSV: {str(e)}'})
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.debug(f"Cleaned up temporary file: {filepath}")
        
        logger.warning(f"Invalid file type: {file.filename}")
        return jsonify({'error': 'Invalid file type'})
    
    except Exception as e:
        error_msg = log_error(e, "Error in upload_file endpoint")
        return jsonify({'error': str(e)})
    finally:
        if start_time:
            upload_time = end_performance_tracking(start_time)
            logger.debug(f"File upload processing time: {upload_time:.2f} seconds")

@app.route('/query', methods=['POST'])
def query_data():
    start_time = start_performance_tracking()
    try:
        logger.info("Query request received")
        
        data = request.json
        query = data.get('query')
        if not query:
            logger.warning("No query provided")
            return jsonify({'error': 'No query provided'})
        
        if current_data['df'] is None:
            logger.warning("No file data loaded")
            return jsonify({'error': 'No file uploaded. Please upload a file first.'})
        
        try:
            # Process the query using Gemini
            logger.info(f"Processing query: {query[:100]}...")
            response = process_query(current_data['df'], query, current_data['chat_history'])
            
            # Update chat history
            current_data['chat_history'].append({
                'user': query,
                'assistant': response,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'response': response,
                'chat_history': current_data['chat_history']
            })
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return jsonify({'error': 'An error occurred processing your query.'})
    
    except Exception as e:
        error_msg = log_error(e, "Error in query_data endpoint")
        return jsonify({'error': str(e)})
    finally:
        if start_time:
            query_time = end_performance_tracking(start_time)
            logger.debug(f"Query endpoint processing time: {query_time:.2f} seconds")

@app.route('/clear-chat', methods=['POST'])
def clear_chat():
    try:
        logger.info("Clearing chat history")
        current_data['chat_history'] = []
        return jsonify({'success': True})
    except Exception as e:
        error_msg = log_error(e, "Error clearing chat history")
        return jsonify({'error': str(e)})

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions"""
    error_msg = log_error(e, "Unhandled exception")
    return jsonify({
        "error": "Internal server error",
        "message": str(e),
        "timestamp": datetime.now().isoformat()
    }), 500

# Add a debug endpoint for development
if DEBUG_CONFIG['ENABLED']:
    @app.route('/debug/status', methods=['GET'])
    def debug_status():
        try:
            # Convert DataFrame to serializable format if it exists
            df_info = None
            if current_data['df'] is not None:
                df = current_data['df']
                df_info = {
                    'shape': df.shape,
                    'columns': df.columns.tolist(),
                    'dtypes': df.dtypes.astype(str).to_dict()
                }

            return jsonify({
                'debug_config': DEBUG_CONFIG,
                'current_data': {
                    'df_info': df_info,
                    'chat_history': current_data['chat_history']
                },
                'environment': {
                    'flask_env': os.getenv('FLASK_ENV'),
                    'debug_mode': app.debug,
                    'python_version': sys.version,
                },
                'memory_usage': {
                    'used': sys.getsizeof(current_data) if current_data else 0
                }
            })
        except Exception as e:
            error_msg = log_error(e, "Error in debug_status endpoint")
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(port="8080")

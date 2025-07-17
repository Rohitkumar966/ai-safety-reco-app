import streamlit as st
import requests
import json
import os # Import the os module to access environment variables

# --- Configuration ---
# Your Gemini API key. In a real application, this should be loaded securely
# from environment variables or a configuration file.
# For Canvas environment, leave it empty as it's automatically provided at runtime.
# If running locally, you might need to set this as an environment variable
# or replace with your actual key for testing if not using a secure method.
API_KEY = "AIzaSyCjTAbS-0NvtMwx3bjmxgvX0bYTBftMo4M" # This will be populated by the Canvas environment
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# --- Function to generate recommendations (copied from ai-safety-reco-engine-python Canvas) ---
def generate_recommendations(safety_observation: str, hazard_details: str) -> str:
    """
    Generates safety recommendations using the Gemini API based on provided
    safety observation and hazard details.

    Args:
        safety_observation (str): The observed safety issue.
        hazard_details (str): Detailed information about the hazard.

    Returns:
        str: AI-generated recommendations in a brief, bulleted format,
             or an error message if generation fails.
    """
    # Construct the prompt for the AI model
    # The prompt is designed to get brief, 5-10 word bullet points (2-5 points)
    # with no introductory text.
    prompt = f"""Given the following safety observation and hazard details, provide 2 to 5 specific and actionable recommendations to mitigate the hazard and improve safety.
Each recommendation should be a brief bulleted point, strictly 5-10 words long, focusing only on the exact action to be taken. Do not include any introductory or descriptive text before the bullet points.

Safety Observation: "{safety_observation}"
Hazard Details: "{hazard_details}"
"""

    # Prepare the payload for the Gemini API request
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    # --- Proxy Configuration ---
    # Check for proxy environment variables and configure requests to use them.
    # This is crucial if you are behind a corporate proxy that requires authentication.
    proxies = {}
    if os.environ.get("HTTP_PROXY"):
        proxies["http"] = os.environ["HTTP_PROXY"]
    if os.environ.get("HTTPS_PROXY"):
        proxies["https"] = os.environ["HTTPS_PROXY"]
    # Example for setting proxy environment variables (replace with your actual proxy):
    # For Windows Command Prompt:
    # set HTTP_PROXY=http://username:password@your.proxy.server:port
    # set HTTPS_PROXY=http://username:password@your.proxy.server:port
    # For Linux/macOS Terminal:
    # export HTTP_PROXY="http://username:password@your.proxy.server:port"
    # export HTTPS_PROXY="http://username:password@your.proxy.server:port"
    # Make sure to include "http://" or "https://" prefix and port number.
    # If no authentication is needed, just "http://your.proxy.server:port"

    try:
        # Make the POST request to the Gemini API
        # The API_KEY will be automatically provided by Canvas runtime if running here.
        # If running locally, ensure API_KEY is set correctly.
        response = requests.post(
            f"{API_URL}?key={API_KEY}",
            headers=headers,
            data=json.dumps(payload),
            proxies=proxies # Pass the configured proxies here
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        result = response.json()

        # Check if the response contains valid content
        if result.get("candidates") and len(result["candidates"]) > 0 and \
           result["candidates"][0].get("content") and \
           result["candidates"][0]["content"].get("parts") and \
           len(result["candidates"][0]["content"]["parts"]) > 0:
            text = result["candidates"][0]["content"].get("parts")[0].get("text", "No text found.")
            return text
        else:
            return "No recommendations could be generated. The AI response was empty or malformed."

    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error occurred: {http_err}"
        if response.status_code == 400:
            error_message += f" - Bad Request. Check your input or API key."
        elif response.status_code == 401:
            error_message += f" - Unauthorized. Check your API key."
        elif response.status_code == 407: # Specifically handle Proxy Authentication Required
            error_message += f" - Proxy Authentication Required. Please check your proxy settings and credentials."
        elif response.status_code == 429:
            error_message += f" - Too Many Requests. Rate limit exceeded."
        return f"Failed to generate recommendations: {error_message}. Response: {response.text}"
    except requests.exceptions.ConnectionError as conn_err:
        return f"Failed to connect to the API: {conn_err}. Check your internet connection or proxy settings."
    except requests.exceptions.Timeout as timeout_err:
        return f"API request timed out: {timeout_err}."
    except requests.exceptions.RequestException as req_err:
        return f"An unexpected error occurred during the API request: {req_err}."
    except json.JSONDecodeError as json_err:
        return f"Failed to parse API response: {json_err}. Response: {response.text}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# --- Streamlit App Layout ---
st.set_page_config(page_title="AI Safety Recommendations", layout="centered")

st.title("💡 AI-Powered Safety Recommendation Engine")
st.markdown("Enter safety observations and hazard details, and get brief, actionable recommendations.")

# Input fields
st.subheader("Safety Observation")
safety_observation_input = st.text_area(
    "Describe the safety observation:",
    placeholder="e.g., 'Loose wiring observed near the main electrical panel in the workshop.'",
    height=100,
    key="safety_obs_input"
)

st.subheader("Hazard Details")
hazard_details_input = st.text_area(
    "Provide details about the hazard:",
    placeholder="e.g., 'Risk of electrical shock, short circuit, or fire. Located in high-traffic area.'",
    height=100,
    key="hazard_details_input"
)

# Generate button
if st.button("Generate Recommendations", use_container_width=True, type="primary"):
    if safety_observation_input and hazard_details_input:
        with st.spinner("Generating recommendations..."):
            recommendations = generate_recommendations(safety_observation_input, hazard_details_input)
            st.subheader("AI-Generated Recommendations:")
            st.markdown(recommendations)
    else:
        st.error("Please enter both a safety observation and hazard details to get recommendations.")

st.markdown("---")
st.info("This application uses the Gemini API to generate safety recommendations. Always verify recommendations with qualified safety professionals.")

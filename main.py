import pandas as pd
import streamlit as st
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from google.ads.googleads.client import GoogleAdsClient

# Load configuration from google_ads.yaml
#client = GoogleAdsClient.load_from_storage("google_ads.yaml")
# Load environment variables from .env file
# Access the environment variables
developer_token = st.secrets["GOOGLE_ADS_DEVELOPER_TOKEN"]
client_id = st.secrets["GOOGLE_ADS_CLIENT_ID"]
client_secret = st.secrets["GOOGLE_ADS_CLIENT_SECRET"]
refresh_token = st.secrets["GOOGLE_ADS_REFRESH_TOKEN"]

# Create a configuration dictionary directly
config = {
    "developer_token": developer_token,
    "client_id": client_id,
    "client_secret": client_secret,
    "refresh_token": refresh_token,
    "use_proto_plus": True,
}

# Initialize the Google Ads Client directly with config
# client = GoogleAdsClient.load_from_storage(config)
client = GoogleAdsClient.load_from_dict(config)

def fetch_campaign_data(client, customer_id):
    try:
        query = """
            SELECT campaign.id, campaign.name, metrics.impressions, metrics.clicks, metrics.cost_micros 
            FROM campaign 
            WHERE segments.date DURING LAST_30_DAYS
        """
        ga_service = client.get_service("GoogleAdsService")
        response = ga_service.search_stream(customer_id=customer_id, query=query)
        
        campaigns = []
        for batch in response:
            for row in batch.results:
                campaigns.append({
                    "Campaign ID": row.campaign.id,
                    "Campaign Name": row.campaign.name,
                    "Impressions": row.metrics.impressions,
                    "Clicks": row.metrics.clicks,
                    "Cost (USD)": row.metrics.cost_micros / 1_000_000  # Convert micros to USD
                })
        
        if not campaigns:
            raise ValueError("No customer found for the provided customer id.")

        return pd.DataFrame(campaigns)
    except Exception as e:
        raise ValueError(f"Error fetching data: {e}")

def plot_campaign_data(data):
    # Create a bar chart using Matplotlib
    plt.figure(figsize=(10, 5))
    plt.bar(data['Campaign Name'], data['Impressions'], color='blue', label='Impressions')
    plt.bar(data['Campaign Name'], data['Clicks'], color='orange', label='Clicks', alpha=0.7)
    
    plt.xlabel('Campaign Name')
    plt.ylabel('Metrics')
    plt.title('Campaign Performance')
    plt.xticks(rotation=45)
    plt.legend()
    
    # Show the plot in Streamlit
    st.pyplot(plt)

# Streamlit UI
st.title("Ad Campaign Analysis Tool")

customer_id = st.text_input("Enter Your Customer ID:", "")

if st.button("Analyze"):
    if customer_id:
        try:
            data = fetch_campaign_data(client, customer_id)
            st.write(data)

            # Display the data as a table
            st.dataframe(data)

            # Plot campaign performance data
            plot_campaign_data(data)
            
        except ValueError as e:
            st.error(str(e))
    else:
        st.warning("Please enter a valid Customer ID.")

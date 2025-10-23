import streamlit as st
import pandas as pd
import pymysql
from datetime import datetime

# Database Connection 
def create_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='ashu',
            database='secure_check',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as error:
        st.error(f"Database connection error: {error}")
        return None

# Fetch Data
def fetch_data(query):
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                df = pd.DataFrame.from_records(result)
                return df
        finally:
            connection.close()
    else:
        return pd.DataFrame()
    
# Fetch Unique Options for Form
def fetch_unique_values(column_name):
    query = f"SELECT DISTINCT {column_name} FROM policelog ORDER BY {column_name}"
    df = fetch_data(query)
    if not df.empty:
        return df[column_name].tolist()
    return []

# Streamlit Dashboard
st.title("🚨 SecureCheck: Digital Ledger for Police Post Logs")
st.markdown("Real-time monitoring and insights for law enforcement officers.")

# Display Full Table
st.header("📒 Police Log Overview")
data_query = "SELECT * FROM policelog"
data = fetch_data(data_query)
st.dataframe(data, use_container_width=True)

# Insight Queries
st.header("💫 Advanced Insights")
selected_query = st.selectbox("Select a query to run:", [
    "What are the top 10 vehicle_Number involved in drug-related stops?",
    "Which vehicles were most frequently searched?",
    "Which driver age group had the highest arrest rate?",
    "What is the gender distribution of drivers stopped in each country?",
    "Which race and gender combination has the highest search rate?",
    "What time of day sees the most traffic stops?",
    "What is the average stop duration for different violations?",
    "Are stops during the night more likely to lead to arrests?",
    "Which violations are most associated with searches or arrests?",
    "Which violations are most common among younger drivers (<25)?",
    "Is there a violation that rarely results in search or arrest?",
    "Which countries report the highest rate of drug-related stops?",
    "What is the arrest rate by country and violation?",
    "Which country has the most stops with search conducted?",
    "Yearly Breakdown of Stops and Arrests by Country",
    "Driver Violation Trends Based on Age and Race",
    "Time Period Analysis of Stops (Joining with Date Functions) , Number of Stops by Year,Month, Hour of the Day",
    "Violations with High Search and Arrest Rates",
    "Driver Demographics by Country (Age, Gender, and Race)",
    "Top 5 Violations with Highest Arrest Rates"
])

# Query Map 
query_map = {
    # Vehicle-Based
    "What are the top 10 vehicle_Number involved in drug-related stops?" :
        "SELECT vehicle_number, COUNT(*) AS drug_stop_count FROM policelog WHERE drugs_related_stop=1 GROUP BY vehicle_number ORDER BY drug_stop_count DESC LIMIT 10",

    "Which vehicles were most frequently searched?" :
        "SELECT vehicle_number, COUNT(*) AS search_count FROM policelog WHERE search_conducted='Yes' GROUP BY vehicle_number ORDER BY search_count DESC LIMIT 10",

    # Demographic-Based
    "Which driver age group had the highest arrest rate?" :
        "SELECT CASE WHEN driver_age<25 THEN '<25' WHEN driver_age BETWEEN 25 AND 40 THEN '25-40' WHEN driver_age BETWEEN 41 AND 60 THEN '41-60' ELSE '60+' END AS age_group, ROUND(SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS arrest_rate FROM policelog GROUP BY age_group ORDER BY arrest_rate DESC LIMIT 1",

    "What is the gender distribution of drivers stopped in each country?" :
        "SELECT country_name, driver_gender, COUNT(*) AS total_stops FROM policelog GROUP BY country_name, driver_gender ORDER BY country_name",

    "Which race and gender combination has the highest search rate?" :
        "SELECT driver_race, driver_gender, ROUND(SUM(CASE WHEN search_conducted='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS search_rate FROM policelog GROUP BY driver_race, driver_gender ORDER BY search_rate DESC LIMIT 1",

    # Time & Duration Based
    "What time of day sees the most traffic stops?" :
        "SELECT HOUR(stop_time) AS hour, COUNT(*) AS total_stops FROM policelog GROUP BY hour ORDER BY total_stops DESC LIMIT 1",

    "What is the average stop duration for different violations?" :
        "SELECT violation, ROUND(AVG(CAST(stop_duration AS DECIMAL(10,2))),2) AS avg_duration FROM policelog GROUP BY violation ORDER BY avg_duration DESC",

    "Are stops during the night more likely to lead to arrests?" :
        "SELECT CASE WHEN HOUR(stop_time) BETWEEN 20 AND 23 OR HOUR(stop_time) BETWEEN 0 AND 5 THEN 'Night' ELSE 'Day' END AS time_period, ROUND(SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS arrest_rate FROM policelog GROUP BY time_period",

    # Violation-Based
    "Which violations are most associated with searches or arrests?" :
        "SELECT violation, SUM(CASE WHEN search_conducted='Yes' THEN 1 ELSE 0 END) AS total_searches, SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END) AS total_arrests FROM policelog GROUP BY violation ORDER BY total_searches+total_arrests DESC LIMIT 5",

    "Which violations are most common among younger drivers (<25)?" :
        "SELECT violation, COUNT(*) AS total_cases FROM policelog WHERE driver_age<25 GROUP BY violation ORDER BY total_cases DESC LIMIT 5",

    "Is there a violation that rarely results in search or arrest?" :
        "SELECT violation, ROUND(SUM(CASE WHEN search_conducted='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS search_rate, ROUND(SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS arrest_rate FROM policelog GROUP BY violation HAVING search_rate<1 AND arrest_rate<1",

    # Location-Based
    "Which countries report the highest rate of drug-related stops?" :
        "SELECT country_name, ROUND(SUM(CASE WHEN drugs_related_stop=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS drug_stop_rate FROM policelog GROUP BY country_name ORDER BY drug_stop_rate DESC LIMIT 5",

    "What is the arrest rate by country and violation?" :
        "SELECT country_name, violation, ROUND(SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS arrest_rate FROM policelog GROUP BY country_name, violation ORDER BY arrest_rate DESC",

    "Which country has the most stops with search conducted?" :
        "SELECT country_name, COUNT(*) AS total_searches FROM policelog WHERE search_conducted='Yes' GROUP BY country_name ORDER BY total_searches DESC LIMIT 1",

    # Complex Queries
    "Yearly Breakdown of Stops and Arrests by Country" :
        "SELECT YEAR(stop_date) AS year, country_name, ROUND(SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS arrest_rate FROM policelog GROUP BY year, country_name ORDER BY year, country_name",

    "Driver Violation Trends Based on Age and Race" :
        "SELECT driver_race, CASE WHEN driver_age<25 THEN '<25' WHEN driver_age BETWEEN 25 AND 40 THEN '25-40' WHEN driver_age BETWEEN 41 AND 60 THEN '41-60' ELSE '60+' END AS age_group, violation, COUNT(*) AS total_cases FROM policelog GROUP BY driver_race, age_group, violation ORDER BY total_cases DESC",

    "Time Period Analysis of Stops (Joining with Date Functions) , Number of Stops by Year,Month, Hour of the Day" :
        "SELECT YEAR(stop_date) AS year, MONTH(stop_date) AS month, HOUR(stop_time) AS hour, COUNT(*) AS total_stops FROM policelog GROUP BY year, month, hour ORDER BY year, month, hour",

    "Violations with High Search and Arrest Rates" :
        "SELECT violation, ROUND(SUM(CASE WHEN search_conducted='Yes' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS search_rate, ROUND(SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS arrest_rate FROM policelog GROUP BY violation ORDER BY arrest_rate DESC, search_rate DESC",

    "Driver Demographics by Country (Age, Gender, and Race)" :
        "SELECT country_name, ROUND(AVG(driver_age),1) AS avg_age, COUNT(DISTINCT driver_gender) AS gender_variety, COUNT(DISTINCT driver_race) AS race_variety FROM policelog GROUP BY country_name",

    "Top 5 Violations with Highest Arrest Rates" :
        "SELECT violation, ROUND(SUM(CASE WHEN is_arrested=1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS arrest_rate FROM policelog GROUP BY violation ORDER BY arrest_rate DESC LIMIT 5"
}


# Run Selected Query
if st.button("Run Query"):
    result = fetch_data(query_map[selected_query])
    if not result.empty:
        st.dataframe(result, use_container_width=True)
    else:
        st.warning("No data found for this query.")

st.markdown("************")

# Fetch dynamic options
country_options = fetch_unique_values("country_name")
search_type_options = fetch_unique_values("search_type")
vehicle_options = fetch_unique_values("vehicle_number")
driver_race_options = fetch_unique_values("driver_race")

# Add New Log & Predict
st.header("📕 Add New Police Log & Predict Outcome & Violation")

with st.form("New log form 😇"):
    stop_date = st.date_input("Stop Date")
    stop_time = st.time_input("Stop Time")
    country_name = st.text_input("Country Name")
    driver_gender = st.selectbox("Driver Gender", ["Male", "Female"])
    driver_age = st.number_input("Driver Age", min_value=18, max_value=100, value=25)
    driver_race = st.text_input("Driver Race")
    search_conducted = st.selectbox("Search Conducted", ["0", "1"])
    search_type = st.text_input("Search Type")
    stop_duration = st.selectbox("Stop Duration", ["0", "1"])
    drugs_related_stop = st.selectbox("Was it drug related?", ["Yes", "No"])
    vehicle_number = st.text_input("Vehicle Number")

    submitted = st.form_submit_button("Predict Stop Outcome & Violation")

    if submitted:
        # Convert inputs
        search_conducted_val = int(search_conducted)
        stop_duration_val = int(stop_duration)
        drugs_related_stop_val = 1 if drugs_related_stop == "Yes" else 0

        # Combine date and time
        stop_datetime = datetime.combine(stop_date, stop_time)

        # Filter data for prediction
        filtered_data = data[
            (data["driver_gender"] == driver_gender) &
            (data["driver_age"] == driver_age) &
            (data["stop_duration"] == stop_duration_val) &
            (data["search_conducted"] == search_conducted_val) &
            (data["drugs_related_stop"] == drugs_related_stop_val) &
            (data["country_name"] == country_name) &
            (data["driver_race"] == driver_race) &
            (data["vehicle_number"] == vehicle_number) &
            (data["search_type"] == search_type)
        ]

        # Predict and violation
        if not filtered_data.empty:
            predicted_outcome = filtered_data["stop_outcome"].mode()[0]
            predicted_violation = filtered_data["violation_outcome"].mode()[0]
        else:
            predicted_outcome = "Warning"
            predicted_violation = "Speeding"

        search_text = "A search was conducted" if search_conducted_val else "No search was conducted"
        drug_text = "Was drug related" if drugs_related_stop_val else "Was not found"

        st.markdown(f"""
        **Prediction Summary**
        - Predicted Violation: **{predicted_violation}**
        - Predicted Stop Outcome: **{predicted_outcome}**

        🧚🏻 A {driver_age}-year-old {driver_gender} driver in {country_name} 
        was stopped at {stop_datetime.strftime('%I:%M %p on %Y-%m-%d')}.  
        {search_text}, and the stop {drug_text}.  
        Stop Duration: **{stop_duration_val}**, Vehicle Number: **{vehicle_number}**
        """)
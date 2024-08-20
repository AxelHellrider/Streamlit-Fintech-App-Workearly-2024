from datetime import datetime, timedelta
import altair as alt
import pandas as pd
import streamlit as st
import yfinance as yf
from openai import OpenAI
import os


api_key = st.secrets["openai"]["env_api_key"]
client = OpenAI(api_key=api_key)


def get_stock_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data


st.markdown(
    """
    <style>
    .block-container {
        max-width: 1200px;  /* Adjust the width as needed */
    }
    </style>
    """,
    unsafe_allow_html=True
)

if 'submitted' not in st.session_state:
    st.session_state.submitted = False

if 'stock_data' not in st.session_state:
    st.session_state.stock_data = None
    st.session_state.stock_data2 = None
    st.session_state.combined_data = None


def fetch_data():
    with st.spinner('Fetching data...'):
        try:
            stock_data = get_stock_data(st.session_state.selected_stock,
                                         start_date=st.session_state.selected_start_date,
                                         end_date=st.session_state.selected_end_date)
            stock_data2 = get_stock_data(st.session_state.selected_stock2,
                                          start_date=st.session_state.selected_start_date,
                                          end_date=st.session_state.selected_end_date)
            stock_data = stock_data.rename(columns={'Close': st.session_state.selected_stock})
            stock_data2 = stock_data2.rename(columns={'Close': st.session_state.selected_stock2})
            combined_data = pd.concat([stock_data[st.session_state.selected_stock],
                                       stock_data2[st.session_state.selected_stock2]], axis=1)
            st.session_state.stock_data = stock_data
            st.session_state.stock_data2 = stock_data2
            st.session_state.combined_data = combined_data

        except Exception as e:
            st.error(f"An error occurred while fetching data: {e}")


if not st.session_state.submitted:
    st.title('Interactive Financial Stock Market Comparative Analysis Tool\n(Workearly Assignment)')

    st.session_state.selected_stock = st.text_input('Enter Stock Ticker', 'AAPL').upper()
    st.session_state.selected_stock2 = st.text_input('Enter Another Stock Ticker', 'GOOGL').upper()
    today = datetime.today().date()
    yesterday = today - timedelta(weeks=1)
    st.session_state.selected_start_date = st.date_input('Enter Start Date', yesterday)
    st.session_state.selected_end_date = st.date_input('Enter End Date', today)
    st.session_state.chart_type = st.selectbox('Select Chart Type', ['Line', 'Bar'])

    if st.button('Submit'):
        st.session_state.submitted = True
        fetch_data()
else:
    if st.session_state.stock_data is not None and st.session_state.stock_data2 is not None:
        if st.button('Go back'):
            st.session_state.submitted = False

        # Create columns with the desired widths
        col1, col2, col3 = st.columns(3)  # Adjust the width ratios as needed

        # Display the first stock data in col1
        with col1:
            st.subheader(f"Data for {st.session_state.selected_stock}")
            st.write(st.session_state.stock_data)

            st.subheader(f"Comparative Chart: {st.session_state.selected_stock} vs {st.session_state.selected_stock2}")

            if st.session_state.chart_type == 'Line':
                line_chart = alt.Chart(st.session_state.combined_data.reset_index()).transform_fold(
                    [st.session_state.selected_stock, st.session_state.selected_stock2],
                    as_=['Stock', 'Price']
                ).mark_line().encode(
                    x='Date:T',
                    y='Price:Q',
                    color='Stock:N'
                ).properties(
                    width=750,  # Adjust width to fit within col1 and col2
                    height=400
                )
                st.altair_chart(line_chart)

            elif st.session_state.chart_type == 'Bar':
                bar_chart = alt.Chart(st.session_state.combined_data.reset_index()).transform_fold(
                    [st.session_state.selected_stock, st.session_state.selected_stock2],
                    as_=['Stock', 'Price']
                ).mark_bar().encode(
                    x='Date:T',
                    y='Price:Q',
                    color='Stock:N'
                ).properties(
                    width=750,  # Adjust width to fit within col1 and col2
                    height=400
                )
                st.altair_chart(bar_chart)

        # Display the second stock data in col2
        with col2:
            st.subheader(f"Data for {st.session_state.selected_stock2}")
            st.write(st.session_state.stock_data2)

        # Place the GPT button and later the GPT results in col3
        with col3:
            if st.button('Comparative Performance'):
                with st.spinner('Generating GPT summary...'):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system",
                                 "content": "You are a financial assistant that will retrieve two tables of financial market data and "
                                            "will summarize the comparative performance in text, in full detail with highlights for "
                                            "each stock and also a conclusion with a markdown output. BE VERY STRICT ON YOUR OUTPUT"},
                                {"role": "user",
                                 "content": f"This is the {st.session_state.selected_stock} stock data: {st.session_state.stock_data.to_dict()}, "
                                            f"this is {st.session_state.selected_stock2} stock data: {st.session_state.stock_data2.to_dict()}"}
                            ]
                        )
                        summary = response.choices[0].message.content
                        st.write(summary)
                    except Exception as e:
                        st.error(f"An error occurred with GPT: {e}")
    else:
        st.error('Error: End date must fall after start date.')

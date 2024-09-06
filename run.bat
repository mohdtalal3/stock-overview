@echo off
:: Batch file for setting up and running the Product Stock Management System

:: Install/update dependencies
echo Installing/Updating dependencies...
pip install -r requirements.txt

:: Run the Streamlit application
echo Running the Streamlit application...
streamlit run main.py

:: Wait for user input before closing
echo Application has exited. Press any key to close this window.
pause

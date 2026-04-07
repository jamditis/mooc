@echo off
REM run-update.bat - Entry point for Windows Task Scheduler
REM
REM This batch file runs the Mamdani video update pipeline.
REM Register it as a scheduled task to check for new videos daily.
REM
REM To register manually:
REM   schtasks /Create /SC DAILY /TN "MamdaniVideoUpdate" /TR "C:\Users\amdit\OneDrive\Desktop\mooc\mamdani-video-analysis\scripts\run-update.bat" /ST 08:07
REM
REM To run it once (test):
REM   schtasks /Run /TN "MamdaniVideoUpdate"
REM
REM To delete:
REM   schtasks /Delete /TN "MamdaniVideoUpdate" /F

cd /d "C:\Users\amdit\OneDrive\Desktop\mooc"
python mamdani-video-analysis\scripts\update-pipeline.py 2>&1

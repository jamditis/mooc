@echo off
REM run-update.bat - Entry point for Windows Task Scheduler
REM
REM This batch file runs the Mamdani video update pipeline.
REM It uses %~dp0 to find the repo root relative to this script's location,
REM so it works regardless of where the repo is cloned.
REM
REM To register as a scheduled task:
REM   schtasks /Create /SC DAILY /TN "MamdaniVideoUpdate" /TR "%~f0" /ST 08:07
REM
REM To run it once (test):
REM   schtasks /Run /TN "MamdaniVideoUpdate"
REM
REM To delete:
REM   schtasks /Delete /TN "MamdaniVideoUpdate" /F

REM Navigate to the repo root (two levels up from scripts/)
cd /d "%~dp0..\.."
python mamdani-video-analysis\scripts\update-pipeline.py 2>&1

*** Settings ***
Library    RequestsLibrary

*** Test Cases ***
Health Check API
    Create Session    api    http://localhost:8000
    ${resp}=    GET On Session    api    /health
    Should Be Equal As Strings    ${resp.json()["status"]}    ok
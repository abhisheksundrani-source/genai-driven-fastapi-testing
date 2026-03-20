*** Settings ***
Library    RequestsLibrary
Variables  ../data/generated_cases.json

*** Test Cases ***
Hello API Generated Cases
    Create Session    api    http://localhost:8000
    FOR    ${case}    IN    @{cases}
        ${resp}=    GET On Session    api    /hello/${case["name"]}
        Should Be Equal As Strings    ${resp.json()["message"]}    ${case["expected_message"]}
    END
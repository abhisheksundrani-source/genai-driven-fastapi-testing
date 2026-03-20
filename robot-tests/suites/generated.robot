*** Settings ***
Library    RequestsLibrary
Variables  ../data/generated_cases.json

*** Test Cases ***
Hello API Existing Cases
    Create Session    api    ${BASE_URL}
    FOR    ${case}    IN    @{cases}
        ${name}=    Set Variable    ${case["name"]}
        ${expected}=    Set Variable    ${case["expected_message"]}
        ${resp}=    GET On Session    api    /hello/${name}
        Log    Status: ${resp.status_code}
        Log    Raw response: ${resp.text}
        Should Be Equal As Strings    ${resp.status_code}    200
        ${json}=    Evaluate    json.loads("""${resp.text}""")    json
        Should Be Equal As Strings    ${json["message"]}    ${expected}
    END
*** Settings ***
Documentation     A test suite for valid login.
...               line 2
...               Keywords are imported from the resource file
Resource          keywords.resource
Resource          keywords2.resource
Default Tags      positive
Suite Teardown    Close Server Connection
Suite Setup       Login Admin


*** Test Cases ***
Login User with Password
    [Documentation]  Verifies that a user can successuflly login.
    ...              Topic2:: The documentaiton
    Connect to Server
    Tstep Login User              ironman    1234567890
    Texpect Verify Valid Login    Tony Stark
    [Teardown]    Close Server Connection

Denied Login with Wrong Password
    [Tags]    negative
    Connect to Server
    Run Keyword And Expect Error    *Invalid Password    Login User    ironman    123
    Verify Unauthorised Access
    Login Admin
    [Teardown]    Close Server Connection
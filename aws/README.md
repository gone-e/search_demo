## 함수 Retry 설정하기
1. 내가 정의한 함수의 경우 (Retry Decorator 사용)  
다음과 같이 모든 Excpetion에 대하여 4번 retry 하도록 정의 할 수 있다.  
`retry(ExceptionToCheck, tries=4, delay=1, backoff=2, logger=None)`
```python
from aws.util.retry import retry_function

@retry(Exception, tries=4)
def test_fail(text):
    raise Exception("Fail")
```
특정 Exception 에 대해서만 retry 하도록 설정 할 수 있다.
```python
import random
from aws.util.retry import retry_function

@retry((NameError, IOError), tries=20, delay=1, backoff=1)
def test_multiple_exceptions():
    x = random.random()
    if x < 0.40:
        raise NameError("NameError")
    elif x < 0.80:
        raise IOError("IOError")
    else:
        raise KeyError("KeyError")
```

2. 이미 정의된 함수의 경우 (Retry Function 사용)  
기존 retry 하지 않게 호출하는 함수
```python
query_result = self._get_athena().get_query_results(QueryExecutionId=query_execution_id, NextToken=next_token)
```
retry_function을 이용하여 5번 exponential_retry하도록 설정  
`retry_function(function_name, max_retries, *args, **kwargs)`
```python
from aws.util.retry import retry_function

query_result = retry_function(
    self._get_athena().get_query_results,
    5,
    QueryExecutionId=query_execution_id,
    NextToken=next_token,
)
```
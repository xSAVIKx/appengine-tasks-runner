# Job Service

A simple Flask dockerized application that is just waiting for a random timeout or a timeout
provided in the JSON payload with `sleepTimeoutSeconds` parameter.

Example request:

```json
{
  "sleepTimeoutSeconds": 60
}
```

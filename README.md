AppEngine HTTP Cloud Tasks Runner
------------------

This repo holds a reusable service for handling long-running HTTP Cloud Tasks that
are meant to be sent to other GCP services such as GCF or Cloud Run which require an active
HTTP connection.

# Prerequisites

- [Python 3.10](https://www.python.org/downloads/release/python-3109/)
- [`gcloud` CLI](https://cloud.google.com/sdk/docs/install)

# Architecture

The service is an [App Engine][appengine] service that works in pair with
a [Cloud Tasks][cloud-tasks] queue.

This blend is unique for GCP while tasks that are targeting App Engine standard services
with basic scaling can run for up to 24 hours. We're gonna be using this feature to perform
long-running connections to other deployed services that require a live connection
(e.g. Cloud Functions or Cloud Run).

Here's how such long-running requests may look like:

```mermaid
sequenceDiagram
    actor user
    participant cloudTasks as Cloud Tasks
    participant tasksRunner as Tasks Runner (App Engine)
    participant services as Services
    user->>cloudTasks: schedules an HTTP call task
    cloudTasks->>tasksRunner: sends AppEngine HTTP task
    tasksRunner->>services: sends task payload via authenticated HTTP call
    services->>tasksRunner: sends back a response
    tasksRunner->>cloudTasks: sends back response details
```

It's obvious that in this schema there is no direct way to notify the `caller` about the
HTTP call status so this part is on the service/caller to identify the result of a call.

E.g. one may supply some callback details in the request payload for the `services` to send a
callback before returning HTTP response to the `tasksRunner`.

[appengine]: https://cloud.google.com/appengine

[cloud-tasks]: https://cloud.google.com/tasks

# Infrastructure and setup

The full setup of the required infrastructure is performed with a helper script
[`setup-env.sh`](./setup-env.sh). The script enables required services, creates App Engine
application, service account, queue and secrets.

After the setup is done one may deploy the service using [`deploy.sh`](./deploy.sh) script.

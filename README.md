# SparkScrumBot
Cisco Spark bot to poll each member of the chosen space and post generated answer in the General space

Build on MongoDB and Flask.

There is also a config file config.py, which looks like the following:

```python
#!/usr/bin/env python
bot = {"token": "Your Spark bot token",
       "webhook": "Your Spark web hook id"}

room = {"id": "General space ID"}

apiai = {"token": "Google API.AI access token"}
```

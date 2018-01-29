#!/usr/bin/env python
import yaml

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# printing configuration sections:
# for section in cfg:
#    print(section)
# bot config:
# print(cfg['bot'])
# smartsheet config:
# print(cfg['smartsheet'])


# bot's access token:
print(cfg['bot']['token'])

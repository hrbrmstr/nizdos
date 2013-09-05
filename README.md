nizdos.py
===================================

("nizdos" is an  Ancient Indo-European word for "Nest")

Script to:

- Read heat/AC status from your nest
- Log those variables to Mongo (so you can analyze/visualize it later!)
- Alert you (via Pushover) when heat or AC changes status, whic is primarily why I wrote it

What is "Nest"? An awesome, stylish thermostat that require hacking to get to YOUR data #sigh

    http://nest.com/

Never heard of Pushover? Think #spiffy & easy iOS/Android notifications

    https://pushover.net/

NOT possible without Scott Baker's most excellent pynest interface:

    https://github.com/smbaker/pynest

(I've cut out all but the necessary components of it for use here)

Example usage: Run in cron every ~5 mins:

    */5 * * * * /opt/nest/nizdos.py

I'll be updating the README as well as the repo to add some analysis and visualization code in November 2013

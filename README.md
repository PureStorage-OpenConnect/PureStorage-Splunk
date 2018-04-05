# PureStorage-Splunk
An App &amp; TA for monitoring Pure Storage FlashArrays in a Splunk environment.

The certified and supported versions of these plugins are available for download or install through splunkbase.
App - https://splunkbase.splunk.com/app/3660/
TA - https://splunkbase.splunk.com/app/3659/

## Installation
The App and the TA are installed separately into your splunk environment via one of two methods
1 - You can directly install the versions available in splunkbase
2 - Follow the directions at this link http://docs.splunk.com/Documentation/AddOns/released/Overview/Installingadd-ons

## Usage
In order to pull information from FlashArrays into Splunk, the TA is mandatory since it connects to FlashArrays and
converts the data to a standard Splunk format. The App is optional, but provides a set of pre-configured dashboards which
provide a fleet monitoring experience out of the box.

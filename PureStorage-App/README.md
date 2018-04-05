## Template Table of Contents

### OVERVIEW

- About the PureStorage-App
- Performance benchmarks
- Support and resources

### INSTALLATION

- Hardware and software requirements
- Installation steps
- Deploy to single server instance


### USER GUIDE

- Key concepts
- Data types
- Lookups
- Configure PureStorage-App
- Troubleshooting
- Upgrade
- Example Use Case-based Scenario

---
### OVERVIEW

#### About the PureStorage-App

| Author | PureStorage Inc. |
| --- | --- |
| App Version | 1.0 |
| Vendor Products | All Pure Storage FlashArray running Purity 4.8.x or greater. All hardware generations currently supported by Pure will work with this TA |
| Has index-time operations | true, this add-on must be placed on indexers |
| Create an index | true, impacts disk storage |
| Implements summarization | summary index |

The PureStorage-App allows a Splunk® Enterprise administrator to easily monitor their fleet of PureStorage FlashArrays out of the box with a simple, object-based dashboard approach.

## INSTALLATION AND CONFIGURATION

### Hardware and software requirements

#### Hardware requirements

PureStorage-App supports the following server platforms in the versions supported by Splunk Enterprise:

- Windows
- Ubuntu

#### Software requirements

To function properly, PureStorage-App requires the following software:

- Purity 4.8.x or greater on your FlashArrays

#### Splunk Enterprise system requirements

Because this add-on runs on Splunk Enterprise, all of the [Splunk Enterprise system requirements](http://docs.splunk.com/Documentation/Splunk/latest/Installation/Systemrequirements) apply.

#### Download

Download the PureStorage-App from Splunkbase.

#### Installation steps

##### Deploy to single server instance

Follow these steps to install the app in a single server instance of Splunk Enterprise:

1. Go to Splunkbase
2. Search for PureStorage-App
3. Click "Install"

##### Deploy to distributed deployment

Install the PureStorage-App on the Search Head

##### Deploy to distributed deployment with Search Head Pooling

Install the PureStorage-TA on the Search Heads

##### Deploy to distributed deployment with Search Head Clustering

Install the PureStorage-TA on the Seach Heads

## USER GUIDE

### Key concepts for PureStorage-App
-	The PureStorage Splunk Add-On will integrate with and consume raw data from PureStorage FlashArrays and input the resulting data to Splunk Enterprise.

-	The data collected by the add-on will be made available in Splunk Enterprise through the partner Purestorage-App which is also available through Splunkbase


### Data types

This app provides the index-time and search-time knowledge for the following types of data from the PureStorage FlashArray:

**Array Data**

This is data being pulled in from a FlashArray to report health and performance status

- PureStorage-Rest

### Configure PureStorage-App

There is no specific configuration required to get the app running. However, you will need to connect the arrays as data inputs. Please use the following steps to connect an array

1. Go to Settings -> Data Inputs
2. Click "PureStorage Array Rest API"
3. Click "New"
4. Fill out the array name, IP address, username, and password (readonly access required)
5. Change the "Interval" within "More settings" if desired.

### Troubleshoot PureStorage-App

***Problem***
Array is not collecting data despite showing up in the Data Inputs list.

***Cause***
You may have put a FQDN or an incorrect IP address into the Array field.

***Resolution***
Change the configuration and save. It will begin to collect after you have the correct address.

# Wood Watcher
Wood Watcher is a satellite monitoring platform that enhances reforestation efforts with direct communication between certifiers and field personnel, improving reliability in the carbon credit market.
We built it during [TUM.ai Makeathon 2024](https://makeathon.tum-ai.com/).

## Project Description
### Inspiration
Over 90% of buyers rank monitoring and verification as a major factor in carbon credit purchase decisions. This made us think about how certificate issuers can ensure and validate the fulfilment of forestation pledges.

### Business Case
Wood Watcher turns around the idea of forest monitoring - instead of looking at *deforestation*, we consider *aforestation* and *reforestation* to be the bigger opportunity.
Emission certificate issuers face issues related to (1) detection and (2) enforcement in the case of forestation projects. In many cases, these challenges lead to authorities abandoning assurances and independent certification altogether - leaving both money and loads of impact on the table.
Using our platform, we hope to support smaller, lower-trust certification companies in scaling up the value- and impact chain.


### What it does
With Wood Watcher, we aim to provide a platform that combines detection/evaluation of forestation initiatives with the direction actionability.
While we, like many of the other platform presented here today, work with Sentinel-2 L2A data to provide forest segmentation (and achieve a very, very solid score of 96% validation accuracy on the newer version of the Amazon Rainforest dataset), we wanted to move beyond the technical challenge and tackle a fun (yet practical) challenge in UX. Namely: Assuming you are a German speaking data scientist (e.g. for a smaller CO2 certification company)  - if you notice something wrong in the data, what would you do about it?
The way we solve this: If you notice something phishy on one of the satellite images, you can issue an automated phone call to the person responsible on-site directly from the platform and ask them to investigate.
After investigating, they simply call the number back, and tell the AI assistant about the situation in their mother tongue. The transcript is then summarized and integrated directly into the incidence response system of the platform.

### How we built it
We fetch satellite data from [Sentinel Hub](https://www.sentinel-hub.com/). Training was done on the dataset ["Amazon Rainforest dataset for semantic segmentation V2"](https://zenodo.org/records/3994970) using a U-Net architecture implemented in Keras.
The backend is split into two parts - the CV components is hosted on a Hetzner VM while the Communication component (build using Azure Communication Services and Azure Cognitive Services) is hosted on Railway. The frontend is build in Flutter.

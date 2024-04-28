import 'dart:async';
import 'dart:convert';

import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:gap/gap.dart';
import 'package:lottie/lottie.dart';
import 'package:tumai/global.dart';

import 'incident.dart';

class IncidentDashboard extends StatelessWidget {

  final String imageNow;
  final List<String> otherImages;

  const IncidentDashboard({super.key, required this.imageNow, required this.otherImages});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Flexible(flex: 1, child: CloseButtonRow()),
        Flexible(flex: 6, child: ImageSection(otherImages: otherImages, imageNow: imageNow,)), // Image
        Flexible(flex: 4, child: IncidentSection()), // History
      ],
    );
  }
}

class CloseButtonRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topRight,
      child: GestureDetector(
        child: const Padding(
          padding: EdgeInsets.only(top: 18.0, right: 18.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              Text("Close"),
              Gap(4),
              Icon(Icons.close),
            ],
          ),
        ),
        onTap: () {
          // TODO: Close
          print("Close the dashboard!");
        },
      ),
    );
  }
}

class ImageSection extends StatelessWidget {

  final List<String> otherImages;
  final String imageNow;

  ImageSection({required this.otherImages, required this.imageNow});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        ImageRotationWidget(images: otherImages),
        ImageWidget(base64encodedImage: imageNow),
      ],
    );
  }
}

class ImageRotationWidget extends StatefulWidget {
  final List<String> images;

  const ImageRotationWidget({super.key, required this.images});

  @override
  State<ImageRotationWidget> createState() => _ImageRotationWidgetState();
}

class _ImageRotationWidgetState extends State<ImageRotationWidget> {

  int rotator = 0;

  @override
  void initState() {
    super.initState();
    Timer.periodic(const Duration(milliseconds: 4321), (timer) {
      setState(() {
        rotator++;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return ImageWidget(base64encodedImage: widget.images[rotator]);
  }
}

class ImageWidget extends StatelessWidget {
  final String base64encodedImage;

  const ImageWidget({super.key, required this.base64encodedImage});
  @override
  Widget build(BuildContext context) {
    return Image.memory(base64Decode(base64encodedImage));
  }

}

class IncidentSection extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        IncidentTitleRow(),
        const StatisticsRow(values: {'-10%':'Wach', '69420':'Merge Conflicts', '100%': 'Spaß'}),
        const Expanded(child: IncidentList())
      ],
    );
  }
}

class IncidentTitleRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [const IncidentTitle(title: '1.123123, 32.123432'),
        IncidentActionButtonRow()],
    );
  }

}

class IncidentTitle extends StatelessWidget {

  final String title;

  const IncidentTitle({super.key, required this.title});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topLeft,
      child: Padding(
        padding: const EdgeInsets.only(left: 16.0),
        child: Text(title,
        style: const TextStyle(
          color: Colors.black,
          fontSize: 40,
          fontWeight: FontWeight.w700
        ),),
      ),
    );
  }
}

class StatisticsRow extends StatelessWidget {
  final Map<String, String> values;

  const StatisticsRow({super.key, required this.values});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: values.entries
          .map((e) => StatisticsText(value: e.key, subtext: e.value))
          .toList(),
    );
  }
}

class StatisticsText extends StatelessWidget {
  final String value;
  final String subtext;

  const StatisticsText({super.key, required this.value, required this.subtext});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
              fontSize: 32, fontWeight: FontWeight.w400, color: Colors.blue),
        ),
        const Gap(4),
        Text(
          subtext,
          style: const TextStyle(
              fontSize: 16, fontWeight: FontWeight.w200, color: Colors.black54),
        )
      ],
    );
  }
}

class IncidentActionButtonRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [ResolveIncidentButton(), const Gap(12), AddPersonButton()],
    );
  }
}

class IncidentList extends StatelessWidget {
  const IncidentList({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder(valueListenable: incidents,
    builder: (BuildContext context, List<Incident> value, Widget? child) {
      return ListView.separated(itemBuilder: (context, index) {
        return IncidentCard(title: value[index].title, timestamp: value[index].timestamp.toIso8601String(), report: value[index].content);
      }, separatorBuilder: (context, index) => Container(height: 0), itemCount: value.length);
    });
  }
}

class ResolveIncidentButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return TextButton(
        onPressed: () {
          // TODO: Add add person functionality
          print("Resolve incident pressed");
        },
        child: const Row(
          children: [
            Icon(Icons.done_all_outlined),
            Gap(4),
            Text('Resolve Incident', style: TextStyle(
              fontSize: 32
            ),),
          ],
        ));
  }
}

class AddPersonButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return TextButton(
        onPressed: () {
          // TODO: Add add person functionality
          print("Add person pressed");
        },
        child: const Row(
          children: [
            Icon(Icons.person_add_alt),
            Gap(4),
            Text('Add Person', style: TextStyle(
                fontSize: 32
            )),
          ],
        ));
  }
}

class IncidentCard extends StatelessWidget {
  final String title;
  final String timestamp;
  final String report;

  const IncidentCard(
      {super.key,
      required this.title,
      required this.timestamp,
      required this.report});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 120,
      width: 500,
      child: Material(
        child: Card(
          margin: const EdgeInsets.all(12),
          color: Colors.white,
          shape: const RoundedRectangleBorder(
              borderRadius: BorderRadius.all(Radius.circular(16))),
          elevation: 6,
          child: Stack(
            children: [
              Align(
                alignment: Alignment.topLeft,
                child: Text(
                  title,
                  style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w400,
                      color: Colors.black87),
                ),
              ),
              Align(
                alignment: Alignment.topRight,
                child: Text(
                  timestamp,
                  style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w200,
                      color: Colors.black54),
                ),
              ),
              Align(
                alignment: Alignment.topLeft,
                child: Padding(
                  padding: const EdgeInsets.only(top: 32.0),
                  child: Text(
                    report,
                    style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w200,
                        color: Colors.black54),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}


class LoadingIndicator extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Lottie.network(
              'https://lottie.host/c63d9754-1947-422b-997e-e1fc1875ea48/7MxCiNgUaP.json',
              width: 200,
              height: 200),
          const Gap(16),
          const Text('Loading...'),
        ],
      ),
    );
  }
}
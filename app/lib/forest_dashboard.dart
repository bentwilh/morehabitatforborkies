import 'package:blurrycontainer/blurrycontainer.dart';
import 'package:flutter/material.dart';
import 'package:lottie/lottie.dart';
import 'package:tumai/repository.dart';

enum ForestDashboardState {
  loading,
  error,
  dataLoaded,
}

class ForestDashboard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
          top: 48,
          right: 36,
          left: MediaQuery.of(context).size.width / 3,
          bottom: 48),
      child: SizedBox.expand(
          child: BlurryContainer(
              padding: const EdgeInsets.all(0),
              borderRadius: const BorderRadius.all(Radius.circular(36)),
              child: Container(
                  decoration: BoxDecoration(
                      borderRadius: const BorderRadius.all(Radius.circular(36)),
                      border: Border.all(color: Colors.green, width: 6)),
                  child: ForestDashboardWidget()))),
    );
  }
}

class ForestDashboardWidget extends StatefulWidget {
  @override
  _ForestDashboardWidgetState createState() => _ForestDashboardWidgetState();
}

class _ForestDashboardWidgetState extends State<ForestDashboardWidget> {
  ForestDashboardState _dashboardState = ForestDashboardState.loading;
  List<ForestChangeData>? _forestData;
  DateTime _selectedDate = DateTime.now();
  int _currentStep = 0;
  @override
  void initState() {
    super.initState();
    fetchData();
  }

  Future<void> fetchData() async {
    setState(() {
      _dashboardState = ForestDashboardState.loading;
    });
    // Simulate fetching data with delay.
    await Future.delayed(Duration(seconds: 2));
    // Update the state based on fetched data or error.
    setState(() {
      // Simplified fake data for demonstration purposes
      _forestData = [
        ForestChangeData(
          captureDate: DateTime.now(),
          captureImage:
              'assets/demo_forest.jpg', // Use actual Base64 decoded data in real scenario
          diffOverlay: 'assets/demo_diff_overlay.jpg',
          vitalityScore: 80,
        ),
        // Add more items if needed.
      ];
      _dashboardState = ForestDashboardState.dataLoaded;
    });
  }

  @override
  Widget build(BuildContext context) {
    switch (_dashboardState) {
      case ForestDashboardState.loading:
        return Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Lottie.network(
                  'https://lottie.host/c63d9754-1947-422b-997e-e1fc1875ea48/7MxCiNgUaP.json',
                  width: 100,
                  height: 100),
              SizedBox(height: 16),
              Text('Loading...'),
            ],
          ),
        );
      case ForestDashboardState.error:
        return Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Lottie.network(
                  'https://lottie.host/c63d9754-1947-422b-997e-e1fc1875ea48/7MxCiNgUaP.json',
                  width: 100,
                  height: 100),
              SizedBox(height: 16),
              Text('Error loading data'),
            ],
          ),
        );
      case ForestDashboardState.dataLoaded:
        return _buildDataLoadedLayout();
      default:
        return SizedBox.shrink();
    }
  }

  Widget _buildDataLoadedLayout() {
    return Padding(
      padding: const EdgeInsets.all(8.0),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Column(
              children: [
                _forestData != null && _forestData!.isNotEmpty
                    ? Image.network(
                        'https://www.industrialempathy.com/img/remote/ZiClJf-1920w.jpg')
                    : SizedBox.shrink(),
                Material(
                  child: Slider(

                      value: 0.5,
                      onChanged: (val) {
                        print(val);
                      }),
                )
              ],
            ),
          ),
          Expanded(
              flex: 1,
              child: Column(
                children: [
                  IconButton(
                    icon: Icon(Icons.close),
                    onPressed: () {
                      Navigator.of(context).pop();
                    },
                  ),
                  Text("Buenos Dias"),
                ],
              )),
        ],
      ),
    );
  }

  Widget _buildKPIWidget(String title, num value) {
    return KPIWidget(title, value
        // Add other properties needed for SomeKPIWidget
        );
  }
}

class KPIWidget extends StatelessWidget {
  final String title;
  final num value;

  const KPIWidget(this.title, this.value);

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [Text('$value'), Text(title)],
    );
  }
}

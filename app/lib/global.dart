import 'package:flutter/cupertino.dart';
import 'package:tumai/incident.dart';

ValueNotifier<List<Incident>> incidents = ValueNotifier(<Incident>[
  Incident(title: 'Phone Number', content: "There is no deforestation in my forest!", timestamp: DateTime.now()),
  Incident(title: 'Original Report', content: "Incident reported to local authority", timestamp: DateTime.now()),
]);
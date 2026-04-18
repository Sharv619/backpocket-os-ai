import 'package:flutter/material.dart';
import 'package:backpocket_mvp/screens/billing_screen.dart';

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BackPocket OS',
      initialRoute: '/',
      routes: {
        '/': (context) => HomeScreen(),  // Existing route
        '/billing': (context) => BillingScreen(),  // New Billing route
      },
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
    );
  }
}
import 'package:flutter/material.dart';
import 'package:backpocket_mvp/models/subscription.dart';
import 'package:backpocket_mvp/models/payment.dart';
import 'package:backpocket_mvp/services/api_service.dart';

class BillingScreen extends StatefulWidget {
  @override
  _BillingScreenState createState() => _BillingScreenState();
}

class _BillingScreenState extends State<BillingScreen> {
  final ApiService apiService = ApiService();
  Subscription? _subscription;
  List<Payment>? _payments;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Billing'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            FutureBuilder<Subscription>
              (builder: (context, snapshot) {
                if (snapshot.hasData) {
                  _subscription = snapshot.data;
                  return Text(
                    '${_subscription?.status ?? 'Loading...'}
                    ',
                    style: TextStyle(fontSize: 18),
                  );
                }
                return CircularProgressIndicator();
              }),

            FutureBuilder<List<Payment>>
              (builder: (context, snapshot) {
                if (snapshot.hasData) {
                  _payments = snapshot.data;
                  return ListView.builder(
                    itemCount: _payments?.length ?? 0,
                    itemBuilder: (context, index) {
                      final payment = _payments![index];
                      return ListTile(
                        title: Text('₽ $_payment.amount'),
                        subtitle: Text('${_payment.status} - ${_payment.date.toString()}'),
                      );
                    },
                  );
                }
                return Text('No payments yet');
              }),

            ElevatedButton(
              onPressed: () => _initiateCheckout(context),
              child: Text('Pay Now'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _initiateCheckout(BuildContext context) {
    final amount = 29900; // $299.00 in cents
    final successUrl = 'https://yourdomain.com/success';
    final cancelUrl = 'https://yourdomain.com/cancel';

    apiService.
      .createCheckoutSession(
        amount: amount,
        successUrl: successUrl,
        cancelUrl: cancelUrl
      )
      .then((session) {
        // Handle navigation to payment page or open session URL
        print('Checkout session URL: $session');
      }).catchError((error) {
      print('Checkout error: $error');
    });
  }
}
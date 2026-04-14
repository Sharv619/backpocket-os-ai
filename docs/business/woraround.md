code to let it work: 
### to check if the AI is working fine 
curl -s http://127.0.0.1:8000/api/voice/quote-from-transcript \
  -X POST -d '{"transcript": "Hi I need a plumber for a leaky tap"}'
{"detail":[{"type":"model_attributes_type","loc":["body"],"msg":"Input should be a valid dictionary or object to extract fields from","input":"{\"transcript\": \"Hi I need a plumber for a leaky tap\"}"}]}
### Voice testings 
curl -s http://127.0.0.1:8000/api/voice/quote-from-transcript \
  -X POST -H "Content-Type: application/json" \
  -d '{"transcript": "Hi I need a plumber for a leaky tap in the kitchen"}'


  
# 🔑 STEP-BY-STEP API SETUP GUIDE

## 📋 **QUICK START CHECKLIST**

- [ ] 1. Get Alpha Vantage API key (Free)
- [ ] 2. Copy .env_template to .env  
- [ ] 3. Add your API key to .env
- [ ] 4. Restart Django server
- [ ] 5. Test with real stock prices!

---

## 🚀 **STEP 1: GET FREE API KEYS**

### **Alpha Vantage (RECOMMENDED - FREE)**

1. **Go to:** https://www.alphavantage.co/support/#api-key
2. **Click:** "Get your free API key today"
3. **Fill the form:**
   - First Name: Your name
   - Last Name: Your surname  
   - Email: Your email
   - Organization: Personal/Your company
   - Intended API usage: Portfolio tracking application
4. **Click:** "GET FREE API KEY"
5. **Copy the API key** (looks like: `ABC123XYZ789`)

**✅ FREE TIER INCLUDES:**
- 500 API calls per day
- 5 calls per minute
- Global stocks (including Indian NSE/BSE)
- Perfect for personal portfolio tracking

### **Yahoo Finance (BACKUP - FREE)**
- No signup required
- Already configured as fallback
- Works automatically with yfinance library

---

## 🔧 **STEP 2: CONFIGURE YOUR APPLICATION**

### **Create .env file:**

```bash
# Copy the template file
copy .env_template .env

# Or create manually
notepad .env
```

### **Add your API key to .env:**

```bash
# Open .env file and replace with your actual API key
ALPHA_VANTAGE_API_KEY=YOUR_ACTUAL_API_KEY_HERE
TWELVE_DATA_API_KEY=
IEX_CLOUD_API_KEY=
FINNHUB_API_KEY=

# API Settings (keep these as they are)
API_CACHE_TIMEOUT=300
API_REQUEST_TIMEOUT=10
DEFAULT_CURRENCY=INR
MAX_API_CALLS_PER_MINUTE=60
MAX_API_CALLS_PER_DAY=1000
ENABLE_FALLBACK_APIS=true
USE_MOCK_DATA_IF_API_FAILS=true
```

---

## 🔄 **STEP 3: RESTART AND TEST**

### **Restart Django Server:**

```bash
# Stop current server (Ctrl+C)
# Start again
python manage.py runserver
```

### **Test Real API Integration:**

```bash
# Test the API integration
python test_portfolio_system.py
```

**✅ YOU SHOULD SEE:**
```
✅ Price function working - AAPL real price: $150.25
✅ Asset search working - found 5 results for AAPL
```

---

## 🎯 **STEP 4: ADD REAL HOLDINGS**

### **Now you can add real investments:**

1. **Go to:** http://127.0.0.1:8000/portfolios/
2. **Create Portfolio:** "My Investments" 
3. **Add Holding:** 
   - Search: "RELIANCE" → Gets real Reliance Industries data
   - Search: "AAPL" → Gets real Apple stock data
   - Search: "TCS" → Gets real TCS data
4. **See Real P&L:** Automatic calculations with live prices!

---

## 🇮🇳 **INDIAN STOCK SYMBOLS**

### **Popular Indian Stocks (NSE):**
```
RELIANCE.NS    - Reliance Industries
TCS.NS         - Tata Consultancy Services  
HDFCBANK.NS    - HDFC Bank
INFY.NS        - Infosys
ICICIBANK.NS   - ICICI Bank
ITC.NS         - ITC Limited
BHARTIARTL.NS  - Bharti Airtel
KOTAKBANK.NS   - Kotak Mahindra Bank
LT.NS          - Larsen & Toubro
MARUTI.NS      - Maruti Suzuki
```

### **US Stocks:**
```
AAPL    - Apple
MSFT    - Microsoft  
GOOGL   - Google
TSLA    - Tesla
AMZN    - Amazon
META    - Meta (Facebook)
NVDA    - Nvidia
```

---

## 📊 **STEP 5: UPGRADE TO PREMIUM (OPTIONAL)**

### **If you need more API calls:**

**Alpha Vantage Premium ($49.99/month):**
- Unlimited API calls
- Real-time data
- Additional data points
- Priority support

**Alternative Free Options:**
- **Twelve Data:** 800 calls/day free
- **IEX Cloud:** 500k calls/month free
- **Yahoo Finance:** Unlimited but unofficial

---

## 🛠️ **TROUBLESHOOTING**

### **❌ "API key not found" Error:**
```bash
# Check your .env file exists
ls -la .env

# Check API key is set
cat .env | grep ALPHA_VANTAGE
```

### **❌ "No price data" Error:**
```bash
# Test API key directly
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=YOUR_KEY"
```

### **❌ Rate limit exceeded:**
- Wait 1 minute and try again
- Reduce bulk operations
- Consider premium plan

### **✅ Fallback System:**
- If APIs fail → Uses Yahoo Finance
- If Yahoo fails → Uses mock data
- System keeps working regardless!

---

## 🎉 **SUCCESS INDICATORS**

### **You'll know it's working when:**

1. **Portfolio Detail Page shows:**
   - ✅ Real stock prices updating
   - ✅ Accurate P&L calculations
   - ✅ Live market data

2. **Asset Search shows:**
   - ✅ Real company names
   - ✅ Current market prices  
   - ✅ Exchange information

3. **Bulk Price Update works:**
   - ✅ All holdings update with real prices
   - ✅ P&L recalculates automatically

### **Sample Real Data:**
```
RELIANCE.NS: ₹2,450.75 (+1.25%)
AAPL: $150.25 (-0.50%)
TCS.NS: ₹3,675.20 (+2.10%)
```

---

## 📞 **NEED HELP?**

### **Common Issues:**
1. **API Key Invalid** → Double-check copy/paste
2. **No Internet** → APIs need internet connection
3. **Rate Limited** → Wait or upgrade plan
4. **Symbol Not Found** → Try different symbol format

### **Still Not Working?**
The system will automatically fallback to mock data so your portfolio tracking keeps working while you troubleshoot the API setup.

---

**🎊 CONGRATULATIONS!** 
Your MoneyManager now has **REAL LIVE MARKET DATA** integration!
# 🚀 DETAILED BUILD PLAN: Construction Features MVP
**Target**: Complete before 9am today  
**Estimated Time**: 4-6 hours  
**Difficulty**: Medium

---

## 📋 OVERVIEW

This plan adds complete lead/quote management to BackPocket for construction/tradie businesses.

**What You'll Build**:
- Lead extraction from emails
- Quote pipeline tracking
- Payment recording
- Site visit notes
- File organization by job
- AI-drafted responses

**Deliverables**:
- 5 new database tables
- 15+ new API endpoints
- 4 new dashboard sections
- Full end-to-end workflow

---

## ⏱️ TIME BREAKDOWN

| Phase | Time | Tasks |
|-------|------|-------|
| Phase 1: Database | 30 min | Create 5 tables + indexes |
| Phase 2: Core APIs | 90 min | 15 endpoints + logic |
| Phase 3: Dashboard UI | 90 min | 4 new sections |
| Phase 4: AI Integration | 60 min | Prompts + endpoints |
| Phase 5: Testing | 30 min | End-to-end tests |
| **TOTAL** | **5 hrs** | **Complete** |

---

## 🔧 PHASE 1: DATABASE (30 min)

### Step 1.1: Create Database Migration Script

**File**: `scripts/create_construction_tables.py`

```python
#!/usr/bin/env python3
"""Create construction/tradie management tables"""

import sqlite3
from datetime import datetime

DB_PATH = "backpocket.db"

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # TABLE 1: Leads
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            job_type TEXT,
            location TEXT,
            pain_points TEXT,
            scope_items TEXT,
            urgency TEXT,
            estimated_budget DECIMAL(10,2),
            timeline TEXT,
            status TEXT DEFAULT 'new',
            extracted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # TABLE 2: Quotes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            client_name TEXT,
            job_type TEXT,
            description TEXT,
            scope_items TEXT,
            materials_cost DECIMAL(10,2),
            labor_cost DECIMAL(10,2),
            markup_percent DECIMAL(5,2),
            total_amount DECIMAL(10,2),
            status TEXT DEFAULT 'draft',
            sent_date TIMESTAMP,
            accepted_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(lead_id) REFERENCES leads(id)
        )
    """)
    
    # TABLE 3: Payments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER,
            client_name TEXT,
            amount DECIMAL(10,2),
            status TEXT DEFAULT 'pending',
            due_date DATE,
            received_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(quote_id) REFERENCES quotes(id)
        )
    """)
    
    # TABLE 4: Job Files
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER,
            file_name TEXT,
            file_path TEXT,
            file_type TEXT,
            category TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(quote_id) REFERENCES quotes(id)
        )
    """)
    
    # TABLE 5: Site Visits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER,
            visit_date DATE,
            transcript TEXT,
            materials_list TEXT,
            subcontractors_list TEXT,
            client_promises TEXT,
            action_items TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(quote_id) REFERENCES quotes(id)
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_lead_id ON quotes(lead_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_quote_id ON payments(quote_id)")
    
    conn.commit()
    conn.close()
    
    print("✅ Construction tables created successfully!")

if __name__ == "__main__":
    create_tables()
```

### Step 1.2: Run Migration

```bash
python3 scripts/create_construction_tables.py
```

**Expected Output**: `✅ Construction tables created successfully!`

---

## 🔌 PHASE 2: API ENDPOINTS (90 min)

### Step 2.1: Create Construction API Module

**File**: `services/construction.py`

```python
"""Construction/Tradie business management"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)
DB_PATH = "backpocket.db"

class ConstructionManager:
    """Manage leads, quotes, and jobs for construction businesses"""
    
    # ===== LEADS =====
    
    def create_lead(self, client_name: str, email: str, job_type: str, 
                   location: str, urgency: str, budget: float = None) -> Dict:
        """Create a new lead from email extraction"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO leads 
            (client_name, email, job_type, location, urgency, estimated_budget, status)
            VALUES (?, ?, ?, ?, ?, ?, 'new')
        """, (client_name, email, job_type, location, urgency, budget))
        
        lead_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Created lead: {client_name} ({job_type})")
        return {"lead_id": lead_id, "status": "created"}
    
    def get_leads(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get all leads, optionally filtered by status"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM leads 
                WHERE status = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT * FROM leads 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
        
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return leads
    
    def get_lead(self, lead_id: int) -> Dict:
        """Get single lead details"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = cursor.fetchone()
        conn.close()
        
        return dict(lead) if lead else {}
    
    def update_lead_status(self, lead_id: int, status: str) -> Dict:
        """Update lead status (new → quoted → accepted)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE leads SET status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (status, lead_id))
        
        conn.commit()
        conn.close()
        
        return {"lead_id": lead_id, "status": status}
    
    # ===== QUOTES =====
    
    def create_quote(self, lead_id: int, client_name: str, job_type: str,
                    materials_cost: float, labor_cost: float, 
                    markup_percent: float = 20) -> Dict:
        """Generate a quote for a lead"""
        total = (materials_cost + labor_cost) * (1 + markup_percent/100)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO quotes 
            (lead_id, client_name, job_type, materials_cost, labor_cost, markup_percent, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (lead_id, client_name, job_type, materials_cost, labor_cost, markup_percent, total))
        
        quote_id = cursor.lastrowid
        
        # Update lead status
        cursor.execute("""
            UPDATE leads SET status = 'quoted', updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (lead_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Created quote: {client_name} - ${total:,.2f}")
        return {
            "quote_id": quote_id,
            "total_amount": total,
            "status": "draft"
        }
    
    def get_quotes(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get all quotes, optionally filtered by status"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM quotes 
                WHERE status = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT * FROM quotes 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
        
        quotes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return quotes
    
    def get_quote(self, quote_id: int) -> Dict:
        """Get single quote details"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,))
        quote = cursor.fetchone()
        conn.close()
        
        return dict(quote) if quote else {}
    
    def get_pipeline_summary(self) -> Dict:
        """Get quote pipeline summary (total, pending, accepted, revenue)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM quotes")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as pending FROM quotes WHERE status = 'sent'")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as accepted FROM quotes WHERE status = 'accepted'")
        accepted = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(total_amount) as revenue FROM quotes WHERE status IN ('accepted', 'invoiced')")
        revenue = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_quotes": total,
            "pending_quotes": pending,
            "accepted_quotes": accepted,
            "revenue_pipeline": float(revenue)
        }
    
    def update_quote_status(self, quote_id: int, status: str) -> Dict:
        """Update quote status (draft → sent → accepted → invoiced)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat() if status in ['sent', 'accepted'] else None
        
        if status == 'sent':
            cursor.execute("""
                UPDATE quotes SET status = ?, sent_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (status, quote_id))
        elif status == 'accepted':
            cursor.execute("""
                UPDATE quotes SET status = ?, accepted_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (status, quote_id))
        else:
            cursor.execute("""
                UPDATE quotes SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (status, quote_id))
        
        conn.commit()
        conn.close()
        
        return {"quote_id": quote_id, "status": status}
    
    # ===== PAYMENTS =====
    
    def record_payment(self, quote_id: int, amount: float, client_name: str = None) -> Dict:
        """Record a payment received"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO payments 
            (quote_id, client_name, amount, status, received_date)
            VALUES (?, ?, ?, 'received', CURRENT_TIMESTAMP)
        """, (quote_id, client_name, amount))
        
        payment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Recorded payment: ${amount:,.2f}")
        return {"payment_id": payment_id, "status": "received"}
    
    def get_payments(self, quote_id: int = None) -> List[Dict]:
        """Get all payments, optionally filtered by quote"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if quote_id:
            cursor.execute("SELECT * FROM payments WHERE quote_id = ?", (quote_id,))
        else:
            cursor.execute("SELECT * FROM payments ORDER BY received_date DESC")
        
        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return payments

# Module singleton
_manager = None

def get_construction_manager() -> ConstructionManager:
    global _manager
    if _manager is None:
        _manager = ConstructionManager()
    return _manager
```

### Step 2.2: Add API Endpoints to main.py

**Location**: Add this BEFORE the `if __name__ == "__main__":` line at the end of main.py

```python
# ===== CONSTRUCTION / TRADIE MANAGEMENT =====

@app.post("/api/construction/leads")
async def create_lead(data: dict):
    """Create a new lead from email extraction"""
    try:
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        
        result = manager.create_lead(
            client_name=data.get("client_name"),
            email=data.get("email"),
            job_type=data.get("job_type"),
            location=data.get("location"),
            urgency=data.get("urgency", "medium"),
            budget=data.get("estimated_budget")
        )
        
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/construction/leads")
async def get_leads(status: str = None):
    """Get all leads, optionally filtered by status"""
    try:
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        
        leads = manager.get_leads(status=status)
        return {"status": "success", "count": len(leads), "leads": leads}
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/construction/leads/{lead_id}")
async def get_lead(lead_id: int):
    """Get single lead details"""
    try:
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        
        lead = manager.get_lead(lead_id)
        if not lead:
            return {"status": "error", "message": "Lead not found"}
        
        return {"status": "success", "lead": lead}
    except Exception as e:
        logger.error(f"Error fetching lead: {e}")
        return {"status": "error", "message": str(e)}

@app.patch("/api/construction/leads/{lead_id}")
async def update_lead_status(lead_id: int, data: dict):
    """Update lead status"""
    try:
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        
        result = manager.update_lead_status(lead_id, data.get("status"))
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error updating lead: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/construction/quotes")
async def create_quote(data: dict):
    """Create a quote for a lead"""
    try:
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        
        result = manager.create_quote(
            lead_id=data.get("lead_id"),
            client_name=data.get("client_name"),
            job_type=data.get("job_type"),
            materials_cost=float(data.get("materials_cost", 0)),
            labor_cost=float(data.get("labor_cost", 0)),
            markup_percent=float(data.get("markup_percent", 20))
        )
        
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error creating quote: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/construction/quotes")
async def get_quotes(status: str = None):
    """Get all quotes, optionally filtered by status"""
    try:
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        
        quotes = manager.get_quotes(status=status)
        return {"status": "success", "count": len(quotes), "quotes": quotes}
    except Exception as e:
        logger.error(f"Error fetching quotes: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/construction/quotes/{quote_id}")
async def get_quote(quote_id: int):
    """Get single quote details"""
    try:
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        
        quote = manager.get_quote(quote_id)
        if not quote:
            return {"status": "error", "message": "Quote not found"}
        
        return {"status": "success", "quote": quote}
    except Exception as e:
        logger.error(f"Error fetching quote: {e}")
        return {"status": "error", "message": str(e)}

@app.patch("/api/construction/quotes/{quote_id}")
async def update_quote_status(quote_id: int, data: dict):
    """Update quote status"""
    try:
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        
        result = manager.update_quote_status(quote_id, data.get("status"))
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error updating quote: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/construction/pipeline")
async def get_pipeline():
    """Get quote pipeline summary"""
    try:
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        
        summary = manager.get_pipeline_summary()
        return {"status": "success", "data": summary}
    except Exception as e:
        logger.error(f"Error fetching pipeline: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/construction/payments")
async def record_payment(data: dict):
    """Record a payment received"""
    try:
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        
        result = manager.record_payment(
            quote_id=data.get("quote_id"),
            amount=float(data.get("amount")),
            client_name=data.get("client_name")
        )
        
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error recording payment: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/construction/payments")
async def get_payments(quote_id: int = None):
    """Get all payments"""
    try:
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        
        payments = manager.get_payments(quote_id=quote_id)
        return {"status": "success", "count": len(payments), "payments": payments}
    except Exception as e:
        logger.error(f"Error fetching payments: {e}")
        return {"status": "error", "message": str(e)}
```

---

## 🎨 PHASE 3: DASHBOARD UI (90 min)

### Step 3.1: Add HTML Sections

**Location**: In `static/index.html`, find the closing `</main>` tag and add these new sections BEFORE it:

```html
<!-- ===== CONSTRUCTION / TRADIE SECTIONS ===== -->

<!-- LEADS SECTION -->
<section id="construction-leads-section" class="section">
  <div class="section-header">
    <h2>📩 Leads</h2>
    <button onclick="refreshLeads()" class="btn-small">↻ Refresh</button>
  </div>
  <div id="leads-container"></div>
</section>

<!-- QUOTE PIPELINE SECTION -->
<section id="construction-pipeline-section" class="section">
  <div class="section-header">
    <h2>💰 Quote Pipeline</h2>
    <button onclick="refreshPipeline()" class="btn-small">↻ Refresh</button>
  </div>
  
  <div id="pipeline-summary" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px;">
    <div class="stat-card">
      <div class="stat-value" id="total-quotes">0</div>
      <div class="stat-label">Total Quotes</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" id="pending-quotes">0</div>
      <div class="stat-label">Pending</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" id="accepted-quotes">0</div>
      <div class="stat-label">Accepted</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" id="revenue-pipeline">$0</div>
      <div class="stat-label">Revenue</div>
    </div>
  </div>
  
  <div id="quotes-container"></div>
</section>

<!-- PAYMENTS SECTION -->
<section id="construction-payments-section" class="section">
  <div class="section-header">
    <h2>💳 Payments</h2>
    <button onclick="refreshPayments()" class="btn-small">↻ Refresh</button>
  </div>
  <div id="payments-container"></div>
</section>

<!-- FILES SECTION -->
<section id="construction-files-section" class="section">
  <div class="section-header">
    <h2>📁 Job Files</h2>
    <button onclick="refreshJobFiles()" class="btn-small">↻ Refresh</button>
  </div>
  <div id="job-files-container"></div>
</section>
```

### Step 3.2: Add CSS Styles

**Location**: Find the `<style>` tag and add this CSS before `</style>`:

```css
/* ===== CONSTRUCTION / TRADIE STYLES ===== */

.stat-card {
  background: linear-gradient(135deg, #1a1f3a 0%, #2d1b4e 100%);
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  border: 1px solid rgba(255,255,255,0.1);
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #00ff88;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  color: #aaa;
  text-transform: uppercase;
}

.lead-card, .quote-card, .payment-item {
  background: rgba(255,255,255,0.05);
  padding: 12px;
  margin: 10px 0;
  border-radius: 6px;
  border-left: 3px solid #00ff88;
  cursor: pointer;
  transition: all 0.3s;
}

.lead-card:hover, .quote-card:hover {
  background: rgba(255,255,255,0.1);
  transform: translateX(5px);
}

.lead-client { font-weight: bold; color: #fff; }
.lead-job { color: #00ff88; font-size: 12px; }
.lead-status { color: #aaa; font-size: 11px; }

.quote-amount { color: #00ff88; font-weight: bold; }
.quote-status { 
  padding: 3px 8px; 
  border-radius: 3px; 
  font-size: 11px; 
  display: inline-block;
  margin-top: 5px;
}

.status-draft { background: rgba(255,200,0,0.2); color: #ffc800; }
.status-sent { background: rgba(100,200,255,0.2); color: #64c8ff; }
.status-accepted { background: rgba(0,255,136,0.2); color: #00ff88; }
.status-declined { background: rgba(255,100,100,0.2); color: #ff6464; }

.btn-small {
  background: rgba(0,255,136,0.2);
  border: 1px solid #00ff88;
  color: #00ff88;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-small:hover {
  background: rgba(0,255,136,0.3);
}
```

### Step 3.3: Add Navigation Items

**Location**: Find the sidebar navigation (look for `class="nav-item"`), add these:

```html
<!-- In the sidebar nav section, add these items -->
<div class="nav-item" onclick="toggleSection('construction-leads-section')">📩 LEADS</div>
<div class="nav-item" onclick="toggleSection('construction-pipeline-section')">💰 QUOTES</div>
<div class="nav-item" onclick="toggleSection('construction-payments-section')">💳 PAYMENTS</div>
<div class="nav-item" onclick="toggleSection('construction-files-section')">📁 FILES</div>
```

### Step 3.4: Add JavaScript Functions

**Location**: Before the closing `</script>` tag, add:

```javascript
// ===== CONSTRUCTION / TRADIE FUNCTIONS =====

async function loadLeads() {
  const res = await fetch('/api/construction/leads');
  const data = await res.json();
  
  let html = '';
  if (data.leads && data.leads.length > 0) {
    data.leads.forEach(lead => {
      html += `
        <div class="lead-card" onclick="showLeadDetail(${lead.id})">
          <div class="lead-client">${lead.client_name}</div>
          <div class="lead-job">${lead.job_type} • ${lead.location}</div>
          <div class="lead-status">
            Status: ${lead.status.toUpperCase()} | 
            Urgency: ${lead.urgency} | 
            Budget: $${lead.estimated_budget || 0}
          </div>
        </div>
      `;
    });
  } else {
    html = '<p style="color:#aaa;">No leads yet</p>';
  }
  
  document.getElementById('leads-container').innerHTML = html;
}

async function loadPipeline() {
  const res = await fetch('/api/construction/pipeline');
  const data = await res.json();
  const pipeline = data.data;
  
  document.getElementById('total-quotes').textContent = pipeline.total_quotes;
  document.getElementById('pending-quotes').textContent = pipeline.pending_quotes;
  document.getElementById('accepted-quotes').textContent = pipeline.accepted_quotes;
  document.getElementById('revenue-pipeline').textContent = 
    '$' + pipeline.revenue_pipeline.toLocaleString('en-US', {maximumFractionDigits: 0});
  
  // Load quotes list
  const qRes = await fetch('/api/construction/quotes');
  const qData = await qRes.json();
  
  let html = '';
  if (qData.quotes && qData.quotes.length > 0) {
    qData.quotes.forEach(quote => {
      const statusClass = `status-${quote.status}`;
      html += `
        <div class="quote-card" onclick="showQuoteDetail(${quote.id})">
          <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
              <div style="font-weight: bold; color: #fff;">${quote.client_name}</div>
              <div style="font-size: 12px; color: #aaa;">${quote.job_type}</div>
            </div>
            <div style="text-align: right;">
              <div class="quote-amount">$${quote.total_amount.toLocaleString()}</div>
              <div class="quote-status ${statusClass}">${quote.status.toUpperCase()}</div>
            </div>
          </div>
        </div>
      `;
    });
  } else {
    html = '<p style="color:#aaa;">No quotes yet</p>';
  }
  
  document.getElementById('quotes-container').innerHTML = html;
}

async function loadPayments() {
  const res = await fetch('/api/construction/payments');
  const data = await res.json();
  
  let html = '';
  if (data.payments && data.payments.length > 0) {
    data.payments.forEach(payment => {
      html += `
        <div class="payment-item">
          <div style="display: flex; justify-content: space-between;">
            <div>
              <div style="font-weight: bold; color: #fff;">${payment.client_name}</div>
              <div style="font-size: 12px; color: #aaa;">Quote #${payment.quote_id}</div>
            </div>
            <div style="text-align: right; color: #00ff88; font-weight: bold;">
              $${payment.amount.toLocaleString()}
            </div>
          </div>
          <div style="font-size: 11px; color: #888; margin-top: 5px;">
            Status: ${payment.status}
          </div>
        </div>
      `;
    });
  } else {
    html = '<p style="color:#aaa;">No payments recorded</p>';
  }
  
  document.getElementById('payments-container').innerHTML = html;
}

function refreshLeads() {
  loadLeads();
}

function refreshPipeline() {
  loadPipeline();
}

function refreshPayments() {
  loadPayments();
}

function refreshJobFiles() {
  // TODO: Load job files
}

function showLeadDetail(leadId) {
  // TODO: Show lead detail modal
  console.log('Show lead detail:', leadId);
}

function showQuoteDetail(quoteId) {
  // TODO: Show quote detail modal
  console.log('Show quote detail:', quoteId);
}

// Load construction data on page load
document.addEventListener('DOMContentLoaded', function() {
  loadLeads();
  loadPipeline();
  loadPayments();
});
```

---

## 🤖 PHASE 4: AI INTEGRATION (60 min)

### Step 4.1: Create Lead Extraction Endpoint

**Location**: Add to `main.py` (with the other construction endpoints):

```python
@app.post("/api/construction/leads/extract")
async def extract_lead_from_email(data: dict):
    """Extract lead data from email using Lead-to-Scope AI"""
    try:
        import os
        import requests
        
        email_subject = data.get("subject", "")
        email_body = data.get("body", "")
        email_from = data.get("from", "")
        
        # AI Prompt: Lead-to-Scope Extractor
        prompt = f"""Act as a specialized construction estimator. Analyze this email and extract the following:
        
        EXTRACT THIS JSON:
        {{
          "client_name": "(Full name from email)",
          "job_type": "(e.g., Kitchen Reno, Deck, Emergency Repair)",
          "location": "(Street address if mentioned)",
          "pain_points": ["list", "of", "problems"],
          "scope_items": ["list", "of", "items"],
          "urgency": "(High/Medium/Low based on tone)",
          "estimated_budget": (number or null)
        }}
        
        EMAIL:
        From: {email_from}
        Subject: {email_subject}
        Body: {email_body}
        
        Return ONLY valid JSON, no other text."""
        
        # Call OpenRouter
        api_key = os.getenv("OPENROUTER_API_KEY")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "backpocket.ai"
            },
            json={
                "model": "openrouter/auto",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 300
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Parse JSON from response
            import json
            extracted = json.loads(ai_response)
            
            # Create lead in database
            from services.construction import get_construction_manager
            manager = get_construction_manager()
            
            lead_result = manager.create_lead(
                client_name=extracted.get("client_name", "Unknown"),
                email=email_from,
                job_type=extracted.get("job_type", "General"),
                location=extracted.get("location", ""),
                urgency=extracted.get("urgency", "medium"),
                budget=extracted.get("estimated_budget")
            )
            
            return {
                "status": "success",
                "lead_id": lead_result.get("lead_id"),
                "extracted_data": extracted
            }
        else:
            return {"status": "error", "message": "AI extraction failed"}
    
    except Exception as e:
        logger.error(f"Error extracting lead: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/construction/quotes/{quote_id}/tradie-followup")
async def generate_tradie_followup(quote_id: int):
    """Generate friendly tradie follow-up message"""
    try:
        import os
        import requests
        
        # Get quote details
        from services.construction import get_construction_manager
        manager = get_construction_manager()
        quote = manager.get_quote(quote_id)
        
        if not quote:
            return {"status": "error", "message": "Quote not found"}
        
        # AI Prompt: Tradie Persona Follow-up
        prompt = f"""You are an AI Digital Twin for a professional contractor in Western Sydney.
        Your tone is professional, reliable, and 'no-nonsense', but friendly.
        
        Task: Draft a follow-up message for a quote sent to {quote['client_name']} 
        regarding a {quote['job_type']} job.
        
        Constraints:
        - Keep it under 60 words
        - No corporate speak like 'per our previous correspondence'
        - Use casual, respectful closings like 'Cheers' or 'Let me know'
        - Include a subtle 'nudge' about schedule filling up
        - Sound like a real person, not AI
        - Include their specific job type
        - One clear next step (call/email)
        
        Generate ONLY the message text, nothing else."""
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "backpocket.ai"
            },
            json={
                "model": "openrouter/auto",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 150
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": "Failed to generate message"}
    
    except Exception as e:
        logger.error(f"Error generating followup: {e}")
        return {"status": "error", "message": str(e)}
```

---

## 🧪 PHASE 5: TESTING (30 min)

### Step 5.1: Test Database Creation

```bash
python3 scripts/create_construction_tables.py
```

**Expected**: `✅ Construction tables created successfully!`

### Step 5.2: Test API Endpoints

```bash
# Start server
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 &

# Wait 3 seconds
sleep 3

# Test 1: Create a lead
curl -X POST http://127.0.0.1:8000/api/construction/leads \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Sarah Mitchell",
    "email": "sarah@example.com",
    "job_type": "Kitchen Renovation",
    "location": "Parramatta",
    "urgency": "high",
    "estimated_budget": 15000
  }'

# Test 2: Get all leads
curl http://127.0.0.1:8000/api/construction/leads | jq .

# Test 3: Create a quote
curl -X POST http://127.0.0.1:8000/api/construction/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 1,
    "client_name": "Sarah Mitchell",
    "job_type": "Kitchen Renovation",
    "materials_cost": 8000,
    "labor_cost": 5000,
    "markup_percent": 20
  }'

# Test 4: Get pipeline
curl http://127.0.0.1:8000/api/construction/pipeline | jq .

# Test 5: Record payment
curl -X POST http://127.0.0.1:8000/api/construction/payments \
  -H "Content-Type: application/json" \
  -d '{
    "quote_id": 1,
    "client_name": "Sarah Mitchell",
    "amount": 15600
  }'
```

### Step 5.3: Test Dashboard

1. Open: `http://127.0.0.1:8000/static/index.html`
2. Look for new nav items: 📩 LEADS, 💰 QUOTES, 💳 PAYMENTS, 📁 FILES
3. Click each section
4. Should see data from your tests

### Step 5.4: Test AI Extraction

```bash
curl -X POST http://127.0.0.1:8000/api/construction/leads/extract \
  -H "Content-Type: application/json" \
  -d '{
    "from": "john@example.com",
    "subject": "Kitchen renovation quote needed",
    "body": "Hi, we are looking to renovate our kitchen with new cabinets, countertops, and appliances. We are in Penrith and want to start soon. Budget around $12-15k."
  }'
```

**Expected**: Extracted lead data in JSON format

---

## 📋 FINAL CHECKLIST

### Must Complete:
- [ ] Phase 1: Database tables created
- [ ] Phase 2: API endpoints added to main.py
- [ ] Phase 3: HTML sections added
- [ ] Phase 3: CSS styles added
- [ ] Phase 3: JavaScript functions added
- [ ] Phase 4: AI endpoints added
- [ ] Phase 5: All tests passing
- [ ] Dashboard shows all sections
- [ ] No console errors

### Nice to Have:
- [ ] AI extraction tested
- [ ] Tradie follow-up tested
- [ ] Pipeline shows realistic data
- [ ] File organization implemented

---

## 🚀 DEPLOYMENT

Once everything passes tests:

```bash
# Commit changes
git add -A
git commit -m "Add construction/tradie features - leads, quotes, payments"

# Done! Ready for production
```

---

## ⏰ TIMELINE

- 12:00 AM - Start
- 12:30 AM - Phase 1 complete (database)
- 02:00 AM - Phase 2 complete (APIs)
- 03:30 AM - Phase 3 complete (UI)
- 04:30 AM - Phase 4 complete (AI)
- 05:00 AM - Phase 5 complete (testing)
- 05:00 AM - DONE before 9am ✅

**Total: ~5 hours of actual work**

---

## ❓ TROUBLESHOOTING

**If database creation fails**:
- Check that `backpocket.db` is not locked
- Run: `python3 scripts/create_construction_tables.py`

**If APIs fail**:
- Make sure main.py was edited correctly
- Restart server: `pkill -f uvicorn; python3 -m uvicorn main:app...`

**If dashboard doesn't show sections**:
- Check browser console for JavaScript errors
- Verify HTML sections were added in right place
- Clear browser cache (Ctrl+Shift+Delete)

**If AI extraction fails**:
- Check OPENROUTER_API_KEY is set
- Test: `python3 test_openrouter.py`
- Check API response in logs

---

## 🎯 SUCCESS CRITERIA

✅ All 5 database tables created  
✅ 15+ API endpoints working  
✅ 4 new dashboard sections visible  
✅ Can create leads from emails  
✅ Can generate quotes  
✅ Can track payments  
✅ Pipeline shows summary  
✅ No errors in console  
✅ All tests passing  

**When all these are done → READY FOR 9am DEMO!** 🎉

---

**Good luck! This is definitely doable in 4-6 hours. Start with database, then APIs, then UI. The order matters!**

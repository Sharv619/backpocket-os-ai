# BackPocket Workflows - Detailed Implementation Guide

This document outlines the 4-5 step workflows that automate key business processes.

---

## 📱 Social Media Posting Workflow

**Status:** Ready for Implementation  
**Timeline:** ~3-5 minutes per post  
**Key Twin:** Admin

### Overview
Automatically draft, schedule, and publish social media content with AI assistance.

### The 4-Step Workflow

```
STEP 1: Content Input
    ↓
STEP 2: AI Drafting & Optimization
    ↓
STEP 3: Review & Approval
    ↓
STEP 4: Schedule & Publish
```

### Step-by-Step Breakdown

#### **STEP 1: Content Input** (1 min)
What the user does:
- Open the Social Media section
- Select platform (Instagram, LinkedIn, Twitter)
- Enter content topic or paste raw content
- Add hashtags and mentions (optional)
- Upload images/videos if needed

System stores:
- Raw content in `pending_socials` table
- Platform type and target
- File references in `uploads/`

#### **STEP 2: AI Drafting & Optimization** (1-2 min)
What happens automatically:
- **Admin Twin** analyzes content for tone/length
- Optimizes copy for platform algorithms:
  - Instagram: Hashtag placement, emoji usage
  - LinkedIn: Professional tone, CTAs
  - Twitter: Character limits, thread formatting
- Adds trending hashtags from your history
- Suggests image captions and alt-text
- Runs sentiment analysis

System:
- Calls `POST /api/socials/draft` endpoint
- Uses OpenRouter for creative optimization
- Stores draft in `draft_socials` table with `status='pending_review'`

#### **STEP 3: Review & Approval** (1-2 min)
What the user does:
- Reviews AI draft on dashboard
- Edit if needed (inline editing enabled)
- Add or remove hashtags
- Preview how it looks on platform
- Approve or request changes

System:
- Captures user edits as learning feedback
- Updates draft with corrections
- Stores approval in `approvals` table
- Triggers next step

#### **STEP 4: Schedule & Publish** (30 sec)
What happens:
- User picks posting time (immediate or scheduled)
- System queues post with platform API
- Sends post to: Instagram, LinkedIn, Twitter, etc.
- Tracks engagement metrics
- Logs published content

System:
- Calls platform APIs (via WHAPI/integrations)
- Creates record in `published_socials` table
- Monitors for engagement (likes, comments, shares)
- Stores metrics in `social_metrics` table

### API Endpoints

```bash
# Draft content
POST /api/socials/draft
{
  "platform": "instagram|linkedin|twitter",
  "content": "Raw content text",
  "hashtags": ["tag1", "tag2"],
  "media_files": ["id1", "id2"]
}
→ Returns: { draft_id, optimized_copy, suggestions }

# Approve draft
POST /api/socials/approve
{
  "draft_id": "...",
  "approved_copy": "Final text",
  "schedule_time": "2024-04-15T14:30:00Z" (or null for immediate)
}
→ Returns: { status, post_id, scheduled_for }

# Get metrics
GET /api/socials/metrics?post_id=...
→ Returns: { likes, comments, shares, reach }
```

### Database Tables

```sql
pending_socials (
  id, platform, content, hashtags,
  created_at, status
)

draft_socials (
  id, pending_id, optimized_copy,
  suggestions_json, created_by, status
)

published_socials (
  id, draft_id, platform, final_copy,
  published_at, post_url, scheduled_for
)

social_metrics (
  id, post_id, likes, comments, shares,
  reach, impressions, recorded_at
)
```

---

## 📅 Content Calendar Management Workflow

**Status:** Ready for Implementation  
**Timeline:** ~10-15 minutes per month  
**Key Twin:** Admin (planning), Accountant (budget tracking)

### Overview
Plan, organize, and track content across all channels with team collaboration.

### The 5-Step Workflow

```
STEP 1: Calendar Setup & Planning
    ↓
STEP 2: Content Theme Generation
    ↓
STEP 3: Auto-Draft Multi-Channel Posts
    ↓
STEP 4: Team Review & Collaboration
    ↓
STEP 5: Automated Publishing Schedule
```

### Step-by-Step Breakdown

#### **STEP 1: Calendar Setup & Planning** (3-5 min)
What the user does:
- Open Content Calendar section
- Select time period (week/month/quarter)
- Define content pillars:
  - Educational content
  - Promotional content
  - Community engagement
  - Product launches
- Set posting frequency per platform
- Add team members/collaborators

System:
- Creates calendar layout in UI
- Stores settings in `calendar_config` table
- Initializes empty slots

#### **STEP 2: Content Theme Generation** (2-3 min)
What happens automatically:
- **Admin Twin** analyzes your brand/industry
- Pulls relevant trends from stored documents
- Generates 4-5 content themes for the period
- Groups themes by content pillar
- Suggests optimal posting times

System:
- Calls `POST /api/calendar/generate-themes` endpoint
- Uses RAG to fetch brand guidelines
- Creates entries in `calendar_themes` table

#### **STEP 3: Auto-Draft Multi-Channel Posts** (3-5 min)
What happens:
- For each theme, AI generates drafts for all platforms
- Adapts tone/length for each channel
- Adds platform-specific elements (hashtags, emojis, CTAs)
- Assigns hashtags from your library
- Creates image prompts if needed

System:
- Calls Social Media Posting Workflow Step 2
- Creates `draft_socials` records for each platform
- Links to calendar via `calendar_draft_links` table
- Status: `pending_review_batch`

#### **STEP 4: Team Review & Collaboration** (2-3 min per day)
What happens:
- Dashboard shows calendar with drafts
- Team members can comment on drafts
- Approvers (you) review and approve batch
- Feedback becomes learned patterns
- Final edits captured

System:
- Stores comments in `calendar_comments` table
- Tracks approvals per user
- Logs all changes to `calendar_revisions` table
- Updates learned patterns

#### **STEP 5: Automated Publishing Schedule** (1 min)
What happens:
- Approved posts automatically queue for scheduling
- System spaces them out across the week/month
- Uses optimal posting times from analytics
- Staggered scheduling prevents "all at once" posts
- Monitors engagement and adjusts future scheduling

System:
- Calls Social Media Step 4 in batch
- Creates schedule in `published_socials` with future `scheduled_for` times
- Queues with platform APIs
- Tracks delivery and engagement

### API Endpoints

```bash
# Generate themes for period
POST /api/calendar/generate-themes
{
  "start_date": "2024-04-01",
  "end_date": "2024-04-30",
  "pillars": ["education", "promotion", "engagement"],
  "posting_frequency": {
    "instagram": 5,  # posts per week
    "linkedin": 3,
    "twitter": 10
  }
}
→ Returns: { themes: [...], posting_schedule }

# Batch approve calendar drafts
POST /api/calendar/approve-batch
{
  "calendar_id": "...",
  "approvals": [
    { "draft_id": "...", "approved": true },
    { "draft_id": "...", "approved": false, "feedback": "..." }
  ]
}
→ Returns: { status, queued_count, scheduled_for }

# Get calendar view
GET /api/calendar/view?start=2024-04-01&end=2024-04-30
→ Returns: { calendar_grid, themes, drafts_by_date }
```

### Database Tables

```sql
calendar_config (
  id, user_id, period_start, period_end,
  pillars, posting_frequency, created_at
)

calendar_themes (
  id, calendar_id, theme_name, pillar,
  description, created_at
)

calendar_draft_links (
  id, calendar_id, theme_id, draft_id,
  platform, status
)

calendar_comments (
  id, draft_id, user_id, comment_text, created_at
)

calendar_revisions (
  id, calendar_id, change_type, details, created_at
)
```

---

## 📊 Analytics & Reporting Workflow

**Status:** Ready for Implementation  
**Timeline:** ~5-10 minutes setup, then automatic  
**Key Twin:** Auditor

### Overview
Collect, analyze, and report on business metrics with visual dashboards and insights.

### The 4-Step Workflow

```
STEP 1: Data Source Connection
    ↓
STEP 2: Metric Definition & KPI Setup
    ↓
STEP 3: Auto-Analysis & Insight Generation
    ↓
STEP 4: Report Generation & Alerts
```

### Step-by-Step Breakdown

#### **STEP 1: Data Source Connection** (2-3 min)
What the user does:
- Open Analytics section
- Connect data sources:
  - Google Analytics 4
  - Social Media APIs (Meta, Twitter)
  - Email metrics (open rates, clicks)
  - Sales data (from CRM)
  - Custom data (Google Sheets)
- Authenticate APIs
- Map data fields

System:
- Stores OAuth tokens securely in encrypted DB
- Creates data pipeline jobs
- Schedules daily/hourly sync
- Stores config in `analytics_sources` table

#### **STEP 2: Metric Definition & KPI Setup** (2-3 min)
What the user does:
- Choose KPIs to track:
  - Website traffic (visitors, sessions, bounce rate)
  - Conversion rates
  - Social engagement (reach, impressions, engagement rate)
  - Email performance (open rate, CTR)
  - Sales metrics (revenue, average order value)
  - Operational metrics (response time, processing time)
- Set targets/goals
- Choose visualization type (line, bar, gauge, heatmap)

System:
- Stores KPI definitions in `analytics_kpis` table
- Creates dashboard layout
- Sets up alert thresholds

#### **STEP 3: Auto-Analysis & Insight Generation** (1-2 min, automatic)
What happens automatically (daily/hourly):
- **Auditor Twin** analyzes the metrics
- Identifies trends, anomalies, and outliers
- Compares against historical data
- Identifies correlations between metrics
- Generates human-readable insights:
  - "Social engagement up 23% this week"
  - "Email CTR declining - suggested improvements"
  - "Best performing day: Thursdays at 2PM"

System:
- Scheduled jobs pull latest data
- Calls `POST /api/analytics/analyze` with new data
- OpenRouter generates insights
- Stores analysis in `analytics_insights` table
- Triggers alerts if thresholds breached

#### **STEP 4: Report Generation & Alerts** (2-5 min, automatic)
What happens:
- Weekly/monthly report automatically generated
- Sent to email or dashboard
- Executive summary with key metrics
- Visualizations (charts, heatmaps)
- AI-generated action recommendations
- Comparison to previous period
- Alerts for anomalies or opportunities

System:
- Creates PDF report via ReportLab
- Generates HTML dashboard
- Emails via SendGrid
- Stores report in `analytics_reports` table
- Tracks alert delivery

### API Endpoints

```bash
# Connect data source
POST /api/analytics/connect-source
{
  "source_type": "google_analytics|meta|twitter|custom",
  "auth_token": "...",
  "config": { "property_id": "...", ... }
}
→ Returns: { source_id, status, last_sync }

# Define KPI
POST /api/analytics/kpi/create
{
  "name": "Weekly Revenue",
  "metric": "sum(sales.amount)",
  "granularity": "week",
  "visualization": "line",
  "target": 50000,
  "alert_threshold": 40000
}
→ Returns: { kpi_id }

# Get insights
GET /api/analytics/insights?period=last_30_days
→ Returns: { 
    summary,
    trends: [{metric, change, insight}, ...],
    anomalies: [...],
    recommendations: [...]
  }

# Generate report
POST /api/analytics/report/generate
{
  "period": "monthly",
  "kpi_ids": ["...", "..."],
  "format": "pdf|html|email"
}
→ Returns: { report_id, url, sent_at }
```

### Database Tables

```sql
analytics_sources (
  id, source_type, auth_token,
  config_json, last_sync, created_at
)

analytics_kpis (
  id, name, metric_query, granularity,
  visualization, target, alert_threshold
)

analytics_data (
  id, kpi_id, recorded_date, value,
  metadata_json
)

analytics_insights (
  id, kpi_id, insight_text, trend,
  created_at
)

analytics_reports (
  id, period, format, content,
  sent_to, created_at
)
```

---

## 📧 Newsletter Campaign Manager Workflow

**Status:** Ready for Implementation  
**Timeline:** ~15-20 minutes per campaign  
**Key Twin:** Admin (planning), Accountant (budget)

### Overview
Plan, create, send, and track newsletter campaigns with AI-generated content and A/B testing.

### The 5-Step Workflow

```
STEP 1: Campaign Setup & Audience
    ↓
STEP 2: Content Creation & Personalization
    ↓
STEP 3: Design & Template Selection
    ↓
STEP 4: Preview, Test, & Schedule
    ↓
STEP 5: Send, Track, & Optimize
```

### Step-by-Step Breakdown

#### **STEP 1: Campaign Setup & Audience** (3-5 min)
What the user does:
- Open Newsletter section
- Create new campaign
- Set campaign name, subject, goals
- Select audience:
  - From existing segments
  - By tags/labels
  - By engagement level
  - Custom filters
- Set send time/scheduling

System:
- Creates campaign in `newsletter_campaigns` table
- Pulls audience from contacts/subscribers
- Stores audience snapshot (for consistency)

#### **STEP 2: Content Creation & Personalization** (4-6 min)
What happens:
- **Admin Twin** generates 2-3 content variations
- Options:
  - Use template + fill content
  - Full AI generation based on brief
  - Mix of template + AI
- Personalization elements:
  - {{recipient.first_name}}
  - {{recipient.company}}
  - {{recipient.last_purchase_date}}
  - Dynamic content blocks based on segment

System:
- Drafts stored in `newsletter_drafts` table
- Personalization logic in `draft_content`
- Preview shows actual personalized content

#### **STEP 3: Design & Template Selection** (2-3 min)
What the user does:
- Choose template:
  - Professional (dark mode)
  - Colorful (brand colors)
  - Minimalist (text-focused)
  - Blog excerpt format
- Customize colors/logo
- Add images/video embeds
- Set call-to-action buttons

System:
- Template applied to draft
- Generates responsive HTML
- Preview on mobile/desktop

#### **STEP 4: Preview, Test, & Schedule** (2-3 min)
What the user does:
- Preview full newsletter
- A/B test setup (optional):
  - Version A: Subject line 1
  - Version B: Subject line 2
  - Send to 10% of list first
- Send test email to self
- Schedule sending time
- Set up follow-ups (2-3 days later)

System:
- Renders full email HTML
- Tests email client compatibility
- Schedules via email service
- Creates `newsletter_schedule` record

#### **STEP 5: Send, Track, & Optimize** (ongoing)
What happens:
- Emails sent at scheduled time
- Tracking pixel embedded
- Metrics collected:
  - Delivery rate
  - Open rate
  - Click rate
  - Conversions
- Insights generated daily
- Best practices recommended for next campaign

System:
- Calls email API (SendGrid/etc)
- Tracks opens/clicks via webhooks
- Stores metrics in `newsletter_metrics` table
- Generates insights automatically

### API Endpoints

```bash
# Create campaign
POST /api/newsletter/campaign
{
  "name": "April Launch",
  "subject_line": "Check out what's new",
  "audience_id": "...",
  "goals": ["engagement", "signups"]
}
→ Returns: { campaign_id }

# Generate content
POST /api/newsletter/generate-content
{
  "campaign_id": "...",
  "brief": "Announce new feature with benefits",
  "variations": 3
}
→ Returns: { drafts: [...] }

# Schedule send
POST /api/newsletter/schedule
{
  "campaign_id": "...",
  "draft_id": "...",
  "send_time": "2024-04-15T14:00:00Z",
  "ab_test": {
    "enabled": true,
    "variant_b": "Different subject line",
    "test_percentage": 10
  }
}
→ Returns: { scheduled_id, send_time }

# Get metrics
GET /api/newsletter/metrics?campaign_id=...
→ Returns: {
    sent, delivered, opened, clicked,
    open_rate, ctr, conversions,
    best_links, demographics
  }
```

### Database Tables

```sql
newsletter_campaigns (
  id, name, subject, audience_size,
  goals, created_at, sent_at
)

newsletter_drafts (
  id, campaign_id, content, template,
  personalization_fields, status
)

newsletter_schedule (
  id, campaign_id, draft_id, 
  scheduled_for, ab_variant, send_status
)

newsletter_metrics (
  id, campaign_id, event_type, 
  (delivered|opened|clicked|converted),
  recipient_id, recorded_at
)
```

---

## 🔄 Implementation Priority

**Phase 1 (Immediate - Week 1):**
1. Social Media Workflow (simplest, highest impact)
2. Analytics Workflow (quick ROI)

**Phase 2 (Short-term - Week 2-3):**
3. Content Calendar (depends on social media)
4. Newsletter Manager

**Phase 3 (Medium-term - Week 4+):**
5. Advanced integrations and optimizations

---

## 📝 Notes for Developers

Each workflow follows the same pattern:
- **Input** → User provides data/selections
- **Processing** → AI twin processes with RAG context
- **Review** → User approves with feedback
- **Action** → System executes with APIs
- **Learning** → Feedback becomes learned patterns

All workflows can run standalone or as part of larger automation chains.

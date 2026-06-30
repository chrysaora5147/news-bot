# News Today

เว็บอ่านข่าววันนี้แบบเรียบง่าย เปิดมาแล้วเห็นข่าวทันที และกดกรองข่าวตามหมวดได้

## Features

- แสดงข่าวเด่นของวันนี้
- แสดงข่าวทั้งหมดเป็นการ์ดอ่านง่าย
- กรองข่าวตามหมวด
- ค้นหาข่าวจากหัวข้อ สรุป หรือหมวด
- Responsive ใช้ได้ทั้ง desktop และมือถือ
- GitHub Actions สำหรับดึงข่าวตามเวลา
- รองรับ RSS, Tavily, SerpAPI, Gemini, Supabase และ LINE Messaging API
- แปลหัวข้อและสรุปข่าวเป็นภาษาไทยก่อนแสดงบนเว็บและส่ง LINE
- รวมข่าวซ้ำเป็น story เดียว พร้อมนับจำนวนแหล่งข่าวและคะแนนความดัง
- หน้า admin ที่ `admin.html` สำหรับ approve/reject ข่าวและส่ง LINE เฉพาะข่าวที่ผ่านแล้ว

## Categories

- ข่าวด่วน
- ไทย
- ต่างประเทศ
- เศรษฐกิจ
- หุ้น
- ทองคำ
- คริปโต
- เทคโนโลยี
- ธุรกิจ
- กีฬา

## Run

เปิดไฟล์ `index.html` ใน browser ได้เลย

ถ้ายังไม่ได้ตั้งค่า Supabase เว็บจะใช้ข่าวตัวอย่างใน `app.js` ก่อน

## Setup

1. สร้าง table ใน Supabase ด้วย SQL จาก `supabase/schema.sql`
2. ใส่ `supabaseUrl` และ `supabaseAnonKey` ใน `config.js`
3. ตั้ง GitHub Secrets:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `GEMINI_API_KEY`
   - `TAVILY_API_KEY` ถ้าใช้ Tavily
   - `SERPAPI_API_KEY` ถ้าใช้ SerpAPI
   - `LINE_CHANNEL_ACCESS_TOKEN` ถ้าจะส่ง LINE
   - `LINE_TO_IDS` ถ้าจะส่ง LINE หลายคนให้คั่นด้วย comma
4. ตั้ง Vercel Environment Variables:
   - `ADMIN_TOKEN` token ส่วนตัวสำหรับหน้า admin
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_TO_IDS`
5. ไปที่ Actions > News Pipeline > Run workflow เพื่อทดสอบ
6. เข้า `/admin.html`, ใส่ `ADMIN_TOKEN`, กด approve ข่าวที่ต้องการ แล้วกดส่ง LINE
7. ตั้ง `SEND_LINE_DIGEST=true` ใน GitHub Variables เมื่อต้องการให้ schedule ส่ง LINE อัตโนมัติ

ค่าเริ่มต้นของ pipeline จะไม่ส่ง LINE จากข่าวที่ระบบเสนอทันที ต้องมี `line_approved_at` ก่อน ถ้าต้องการกลับไปส่งอัตโนมัติจากระบบคัดเองให้ตั้ง `LINE_REQUIRE_APPROVAL=false`
ค่าเริ่มต้นของ pipeline จะประมวลผลอย่างน้อย `60` story ต่อรอบ และเว็บจะแสดงเฉพาะข่าวที่ผ่านคะแนนขั้นต่ำ
GitHub Actions ตั้งเวลาไว้ที่ 07:00, 12:00 และ 18:00 ตามเวลาไทย

## Architecture

```text
GitHub Actions
  -> RSS / Tavily / SerpAPI
  -> story clustering + trending score
  -> Gemini Thai translation + summary + category
  -> Supabase articles table
  -> LINE Messaging API

Vercel
  -> host static website
  -> admin approve/reject/send API
  -> read articles from Supabase with anon key
```

## Next Steps

ขั้นต่อไปที่เหมาะกับโปรเจกต์นี้:

1. ปรับหมวดไทยให้ลดข่าวรัฐ/งบประมาณที่ไม่สำคัญ
2. ทำระบบ LINE webhook เพื่อเก็บ userId จากคนที่ add bot
3. เพิ่ม story deduplication ขั้นสูง
4. เพิ่ม API ให้เว็บจัดพอร์ตหรือระบบอื่นดึงข่าวไปใช้ต่อ

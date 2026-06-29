const categories = [
  "ทั้งหมด",
  "ข่าวด่วน",
  "ไทย",
  "การเมือง",
  "เศรษฐกิจ",
  "หุ้น",
  "ต่างประเทศ",
  "ทองคำ",
  "คริปโต",
  "เทคโนโลยี",
  "ธุรกิจ",
  "อสังหา",
  "พลังงาน",
  "กีฬา",
  "บันเทิง",
  "สุขภาพ",
  "ท่องเที่ยว",
  "สิ่งแวดล้อม",
];

const fallbackNews = [
  {
    title: "ครม. ผ่านมาตรการลดค่าครองชีพรอบใหม่",
    category: "เศรษฐกิจ",
    time: "16:30",
    sourceCount: 4,
    summary: "รัฐบาลอนุมัติมาตรการช่วยค่าครองชีพและกระตุ้นการใช้จ่ายระยะสั้น ตลาดจับตาผลต่อค้าปลีกและกำลังซื้อในประเทศ",
    image:
      "url('https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=1200&q=80')",
    hot: true,
  },
  {
    title: "ลิขสิทธิ์บอลโลกคืบหน้า หลังเอกชนเข้าร่วมเจรจา",
    category: "ไทย",
    time: "15:30",
    sourceCount: 4,
    summary: "ดีลถ่ายทอดสดมีสัญญาณบวกมากขึ้น หลังมีภาคเอกชนเข้าร่วมโต๊ะเจรจา แต่ยังต้องรอดูเงื่อนไขค่าใช้จ่ายและสิทธิ์ถ่ายทอด",
    image:
      "url('https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1200&q=80')",
    hot: true,
  },
  {
    title: "SET อ่อนตัวจากแรงขายกลุ่มพลังงาน",
    category: "หุ้น",
    time: "16:10",
    sourceCount: 3,
    summary: "ดัชนีหุ้นไทยถูกกดดันจากหุ้นพลังงานและปิโตรเคมี นักลงทุนรอดูทิศทางราคาน้ำมันและค่าเงินบาทก่อนเพิ่มน้ำหนักลงทุน",
    image:
      "url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80')",
    hot: true,
  },
  {
    title: "ทองคำแกว่งในกรอบ ตลาดรอสัญญาณดอกเบี้ยสหรัฐ",
    category: "ทองคำ",
    time: "13:30",
    sourceCount: 2,
    summary: "ราคาทองยังไม่มีทิศทางชัดเจน ระหว่างแรงหนุนจากความไม่แน่นอนเศรษฐกิจกับแรงกดดันจากบอนด์ยีลด์และดอลลาร์",
    image:
      "url('https://images.unsplash.com/photo-1610375461369-d613b564c245?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
  {
    title: "ค่าเงินบาทผันผวนตามแรงซื้อดอลลาร์",
    category: "เศรษฐกิจ",
    time: "12:20",
    sourceCount: 3,
    summary: "เงินบาทเคลื่อนไหวผันผวนหลังนักลงทุนกลับมาถือดอลลาร์มากขึ้น ฝ่ายวิเคราะห์มองกรอบระยะสั้นยังขึ้นกับข้อมูลเศรษฐกิจสหรัฐ",
    image:
      "url('https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
  {
    title: "หุ้นเทคเอเชียฟื้น หลังตลาดคลายกังวล AI spending",
    category: "เทคโนโลยี",
    time: "11:45",
    sourceCount: 3,
    summary: "หุ้นเทคโนโลยีในเอเชียปรับขึ้นตาม sentiment ตลาดโลก นักลงทุนกลับมาเก็งกำไรในกลุ่มชิปและโครงสร้างพื้นฐาน AI",
    image:
      "url('https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
  {
    title: "ราคาน้ำมันขยับขึ้นจากความเสี่ยงอุปทาน",
    category: "พลังงาน",
    time: "10:50",
    sourceCount: 2,
    summary: "ตลาดน้ำมันจับตาความเสี่ยงด้านอุปทานและท่าทีผู้ผลิตรายใหญ่ ซึ่งอาจกดดันต้นทุนพลังงานและหุ้นที่เกี่ยวข้อง",
    image:
      "url('https://images.unsplash.com/photo-1518709268805-4e9042af2176?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
  {
    title: "ต่างประเทศจับตาเลือกตั้งยุโรปและทิศทางนโยบายเศรษฐกิจ",
    category: "ต่างประเทศ",
    time: "09:40",
    sourceCount: 2,
    summary: "ตลาดโลกติดตามผลเลือกตั้งยุโรป เพราะอาจกระทบทิศทางนโยบายการคลัง การค้า และความเชื่อมั่นสินทรัพย์เสี่ยง",
    image:
      "url('https://images.unsplash.com/photo-1521295121783-8a321d551ad2?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
  {
    title: "คริปโตแกว่งตัว นักลงทุนรอดูเงินไหลเข้า ETF",
    category: "คริปโต",
    time: "09:15",
    sourceCount: 2,
    summary: "ตลาดคริปโตยังแกว่งในกรอบ หลังแรงซื้อระยะสั้นชะลอ นักลงทุนจับตาข้อมูลเงินไหลเข้า ETF และท่าทีดอกเบี้ย",
    image:
      "url('https://images.unsplash.com/photo-1621761191319-c6fb62004040?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
  {
    title: "โรงพยาบาลเอกชนเปิดบริการสุขภาพเชิงป้องกันเพิ่ม",
    category: "สุขภาพ",
    time: "08:50",
    sourceCount: 1,
    summary: "กลุ่มโรงพยาบาลเอกชนเร่งขยายบริการตรวจสุขภาพและแพ็กเกจป้องกันโรค รับความต้องการของกลุ่มวัยทำงานและผู้สูงอายุ",
    image:
      "url('https://images.unsplash.com/photo-1505751172876-fa1923c5c528?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
  {
    title: "ธุรกิจท่องเที่ยวคาดไฮซีซันหนุนรายได้ครึ่งปีหลัง",
    category: "ท่องเที่ยว",
    time: "08:20",
    sourceCount: 2,
    summary: "ผู้ประกอบการท่องเที่ยวมองครึ่งปีหลังยังมีแรงหนุนจากนักท่องเที่ยวต่างชาติและมาตรการกระตุ้นการเดินทางในประเทศ",
    image:
      "url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
  {
    title: "ดีเวลลอปเปอร์จับตาดอกเบี้ย ก่อนเปิดโครงการใหม่",
    category: "อสังหา",
    time: "07:55",
    sourceCount: 2,
    summary: "ตลาดอสังหายังระวังต้นทุนการเงินและกำลังซื้อ ผู้ประกอบการเลือกเปิดโครงการแบบเจาะทำเลมากขึ้น",
    image:
      "url('https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
  {
    title: "ฝุ่นและอากาศแปรปรวนกลับมาเป็นประเด็นในหลายจังหวัด",
    category: "สิ่งแวดล้อม",
    time: "07:30",
    sourceCount: 2,
    summary: "หลายพื้นที่เริ่มเฝ้าระวังคุณภาพอากาศ หลังสภาพอากาศแปรปรวนและมีรายงานค่าฝุ่นเพิ่มขึ้นในบางช่วงเวลา",
    image:
      "url('https://images.unsplash.com/photo-1493246507139-91e8fad9978e?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
  {
    title: "วงการบันเทิงจับตาคอนเสิร์ตใหญ่ปลายปี",
    category: "บันเทิง",
    time: "07:10",
    sourceCount: 1,
    summary: "ผู้จัดงานทยอยประกาศคอนเสิร์ตและอีเวนต์ใหญ่ ทำให้ตลาดบันเทิงสดกลับมาคึกคักในช่วงครึ่งปีหลัง",
    image:
      "url('https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
  {
    title: "ทีมชาติเตรียมประกาศรายชื่อชุดใหม่ก่อนเกมสำคัญ",
    category: "กีฬา",
    time: "06:50",
    sourceCount: 2,
    summary: "แฟนกีฬารอรายชื่อผู้เล่นชุดใหม่ โดยโค้ชเตรียมปรับทีมบางตำแหน่งเพื่อรับมือโปรแกรมแข่งขันถัดไป",
    image:
      "url('https://images.unsplash.com/photo-1459865264687-595d652de67e?auto=format&fit=crop&w=1200&q=80')",
    hot: false,
  },
];

let selectedCategory = "ทั้งหมด";
let searchTerm = "";
let news = fallbackNews;

async function loadSupabaseNews() {
  const config = window.NEWS_CONFIG || {};
  if (!config.supabaseUrl || !config.supabaseAnonKey) {
    return fallbackNews;
  }

  const endpoint = `${config.supabaseUrl.replace(/\/$/, "")}/rest/v1/articles?select=id,title,title_th,summary,summary_th,category,source,url,importance_score,published_at&importance_score=gte.50&order=importance_score.desc&order=published_at.desc&limit=60`;
  const response = await fetch(endpoint, {
    headers: {
      apikey: config.supabaseAnonKey,
      Authorization: `Bearer ${config.supabaseAnonKey}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Supabase request failed: ${response.status}`);
  }

  const rows = await response.json();
  return rows.map((row, index) => ({
    title: row.title_th || row.title,
    category: row.category,
    time: new Date(row.published_at).toLocaleTimeString("th-TH", {
      hour: "2-digit",
      minute: "2-digit",
    }),
    sourceCount: row.source ? 1 : 0,
    summary: row.summary_th || row.summary,
    image: fallbackNews[index % fallbackNews.length].image,
    hot: index < 3 || row.importance_score >= 80,
  }));
}

function filteredNews() {
  return news.filter((item) => {
    const matchesCategory = selectedCategory === "ทั้งหมด" || item.category === selectedCategory;
    const query = searchTerm.trim().toLowerCase();
    const matchesSearch =
      !query ||
      item.title.toLowerCase().includes(query) ||
      item.summary.toLowerCase().includes(query) ||
      item.category.toLowerCase().includes(query);
    return matchesCategory && matchesSearch;
  });
}

function renderCategories() {
  const bar = document.querySelector("#categoryBar");
  bar.innerHTML = categories
    .map(
      (category) =>
        `<button class="category-button ${category === selectedCategory ? "active" : ""}" data-category="${category}">${category}</button>`
    )
    .join("");

  document.querySelectorAll(".category-button").forEach((button) => {
    button.addEventListener("click", () => {
      selectedCategory = button.dataset.category;
      render();
    });
  });
}

function renderTopStory(items) {
  const story = items.find((item) => item.hot) || items[0];
  const container = document.querySelector("#topStory");

  if (!story) {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = `
    <article class="top-card" style="--image: ${story.image}">
      <div>
        <span class="pill">${story.category}</span>
        <h2>${story.title}</h2>
        <p>${story.summary}</p>
      </div>
      <div class="top-meta">
        <span class="pill">${story.time}</span>
        <span class="pill">${story.sourceCount} แหล่งข่าว</span>
      </div>
    </article>
  `;
}

function renderNewsGrid(items) {
  const grid = document.querySelector("#newsGrid");

  if (items.length === 0) {
    grid.innerHTML = `<div class="empty">ไม่เจอข่าวในหมวดนี้ ลองเลือกหมวดอื่นหรือเปลี่ยนคำค้นหา</div>`;
    return;
  }

  grid.innerHTML = items
    .map(
      (item) => `
        <article class="news-card">
          <div class="thumb" style="--image: ${item.image}"></div>
          <div class="news-body">
            <div class="card-meta">
              <span>${item.category}</span>
              <span>${item.time}</span>
            </div>
            <h3>${item.title}</h3>
            <p>${item.summary}</p>
          </div>
        </article>
      `
    )
    .join("");
}

function render() {
  const items = filteredNews();
  renderCategories();
  renderTopStory(items);
  renderNewsGrid(items);

  document.querySelector("#sectionTitle").textContent =
    selectedCategory === "ทั้งหมด" ? "ข่าวทั้งหมดวันนี้" : `ข่าว${selectedCategory}วันนี้`;
  document.querySelector("#resultCount").textContent = `${items.length} ข่าว`;
}

document.querySelector("#searchInput").addEventListener("input", (event) => {
  searchTerm = event.target.value;
  render();
});

loadSupabaseNews()
  .then((items) => {
    news = items.length ? items : fallbackNews;
    render();
  })
  .catch((error) => {
    console.warn(error);
    news = fallbackNews;
    render();
  });

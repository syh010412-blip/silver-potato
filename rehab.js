/**
 * rehab.js — 선영님 왼팔 재활 도우미 CLI
 *
 * 사용법:
 *   node rehab.js          재활 시작 (메인 메뉴)
 *   node rehab.js trends   최근 기록 조회
 *
 * 필요 환경 변수 (.env):
 *   NOTION_API_KEY
 *   NOTION_REHAB_DB_ID  (기본값: a4e01340-cd55-4734-8856-57de6da37217)
 */
require('dotenv').config();
const readline = require('readline');
const { Client } = require('@notionhq/client');

const notion = new Client({ auth: process.env.NOTION_API_KEY });
const REHAB_DB = process.env.NOTION_REHAB_DB_ID || 'a4e01340-cd55-4734-8856-57de6da37217';

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const ask = q => new Promise(r => rl.question(q, r));

function getKSTToday() {
  return new Date(Date.now() + 9 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

async function choose(question, options) {
  while (true) {
    console.log('\n' + question);
    options.forEach((o, i) => console.log(`  [${i + 1}] ${o}`));
    const n = parseInt((await ask('번호 입력: ')).trim()) - 1;
    if (n >= 0 && n < options.length) return n;
    console.log('올바른 번호를 입력해주세요.');
  }
}

// ─── 세션 상태 ───────────────────────────────────────────────────────────────

const session = {
  date: getKSTToday(),
  condition: null,
  mood: null,
  completedSteps: [],
  rangeOfMotion: null,
  painLevel: null,
  memo: null,
};

// ─── 루틴 단계 ───────────────────────────────────────────────────────────────

async function step1() {
  console.log('\n--- 1단계: 어깨 이완 (2분) ---');
  console.log('자세: 편안하게 앉은 상태');
  console.log('동작: 왼쪽 어깨 앞으로 → 위로 → 뒤로 → 내리기  ×5회');
  console.log('포인트: 통증 없는 범위에서만!\n');

  const n = await choose('', ['완료 ✅', '통증 있어요 🛑']);
  if (n === 1) { await handlePain('어깨'); return false; }
  session.completedSteps.push('1단계: 어깨 이완');
  console.log('👍 잘 하셨어요!');
  return true;
}

async function step2() {
  console.log('\n--- 2단계: 왼팔 굴곡·신전 (3분) ---');
  console.log('자세: 팔꿈치 아래 쿠션 받치기');
  console.log('동작: 팔을 천천히 구부렸다 펴기  10회 × 2세트');
  console.log('포인트: 끝까지 다 못 펴도 괜찮아요 💙\n');

  for (let s = 1; s <= 2; s++) {
    const n = await choose(`${s}세트 준비됐으면 골라줘요`, ['완료 ✅', '통증 있어요 🛑']);
    if (n === 1) { await handlePain('팔꿈치'); return false; }
    console.log(`✅ ${s}세트 완료!`);
  }
  session.completedSteps.push('2단계: 왼팔 굴곡·신전');
  return true;
}

async function step3() {
  console.log('\n--- 3단계: 왼팔 수평 거상 (3분) ---');
  console.log('자세: 누운 자세 또는 앉은 자세');
  console.log('동작: 팔을 수평으로 천천히 들어올리기  ×5회');
  console.log('포인트: 작년보다 조금 더 올라가면 대성공!\n');

  const n = await choose('', ['완료 ✅ (평행 이상)', '조금 올라갔어요 (70~80%)', '오늘은 어려워요 (50% 이하)', '통증 있어요 🛑']);
  if (n === 3) { await handlePain('팔 전체'); return false; }

  const romMap = ['평행 이상', '70~80%', '50% 이하'];
  session.rangeOfMotion = romMap[n];
  session.completedSteps.push('3단계: 수평 거상');
  console.log(n === 0 ? '💪 대단해요!' : '💙 오늘도 수고했어요!');
  return true;
}

async function step4() {
  console.log('\n--- 4단계: 왼쪽 견갑골 안정화 (2분) ---');
  console.log('동작: 날갯죽지를 척추 쪽으로 모으기  ×10회');
  console.log('포인트: 왼쪽 날갯죽지 의식하면서\n');

  const n = await choose('', ['완료 ✅', '통증 있어요 🛑']);
  if (n === 1) { await handlePain('날갯죽지'); return false; }
  session.completedSteps.push('4단계: 견갑골 안정화');
  console.log('👍 좋아요!');
  return true;
}

async function step5() {
  console.log('\n--- 5단계: 마무리 이완 (2분) ---');
  console.log('동작: 왼팔 전체 가볍게 털기 + 온찜질 (가능 시)');
  console.log('포인트: 오늘 수고했어요 🎉\n');

  const n = await choose('', ['루틴 완료! 기록할게요 📝', '통증 있어요 🛑']);
  if (n === 1) { await handlePain('전체'); return false; }
  session.completedSteps.push('5단계: 마무리 이완');
  return true;
}

// ─── 루틴 묶음 ───────────────────────────────────────────────────────────────

async function lightRoutine() {
  console.log('\n📋 가벼운 루틴 (2단계) 시작!\n');
  if (!await step1()) return;
  console.log('\n--- 2단계: 온찜질 + 휴식 ---');
  console.log('"오늘은 몸이 쉬고 싶다는 신호예요. 가볍게 하고 푹 쉬는 것도 재활이에요 💙"');
  session.completedSteps.push('2단계: 온찜질 + 휴식');
  await ask('\n온찜질 후 준비되면 Enter를 눌러주세요...');
  await recordCompletion();
}

async function basicRoutine() {
  console.log('\n📋 기본 루틴 (3단계) 시작!\n');
  if (!await step1()) return;
  if (!await step2()) return;
  if (!await step3()) return;
  await recordCompletion();
}

async function fullRoutine() {
  console.log('\n📋 전체 루틴 (5단계) 시작!\n');
  if (!await step1()) return;
  if (!await step2()) return;
  if (!await step3()) return;
  if (!await step4()) return;
  if (!await step5()) return;
  await recordCompletion();
}

// ─── 통증 감지 ───────────────────────────────────────────────────────────────

async function handlePain(location) {
  console.log('\n🛑 지금 바로 멈춰요!');

  const levelIdx = await choose(`통증 강도가 어느 정도예요? (${location})`, [
    '1~3 (약함)', '4~6 (중간)', '7~10 (심함)',
  ]);

  const levelLabels = ['1~3', '4~6', '7+'];
  session.painLevel = levelLabels[levelIdx];

  if (levelIdx === 0) console.log('\n💙 잠깐 쉬고 계속해도 돼요. 조금 쉬어볼게요.');
  else if (levelIdx === 1) console.log('\n⚠️ 오늘은 여기서 마무리해요. 잘 하셨어요!');
  else console.log('\n🚨 치료사 선생님께 꼭 말씀드려요!');

  console.log('\n지금까지 한 것을 기록할게요.\n');
  await recordCompletion();
}

// ─── 완료 기록 & Notion 저장 ─────────────────────────────────────────────────

function romToScore(rom) {
  return { '평행 이상': 10, '70~80%': 8, '50~60%': 6, '30~40%': 4, '30% 이하': 2, '오늘은 별로': 2 }[rom] ?? 5;
}

function painToScore(pain) {
  if (!pain) return 0;
  if (pain === '없음') return 0;
  if (pain.startsWith('1')) return 2;
  if (pain.startsWith('4')) return 5;
  if (pain.startsWith('7')) return 8;
  return 0;
}

async function recordCompletion() {
  console.log('\n=== 오늘 재활 기록 ===');

  if (!session.rangeOfMotion) {
    const n = await choose('왼팔이 얼마나 올라갔어요?', [
      '평행 이상 ✅', '70~80%', '50~60%', '30~40%', '오늘은 별로',
    ]);
    const romLabels = ['평행 이상', '70~80%', '50~60%', '30~40%', '오늘은 별로'];
    session.rangeOfMotion = romLabels[n];
  }

  if (!session.painLevel) {
    const n = await choose('세션 중 통증 수준은?', ['없었어요 😊', '1~3 (약함)', '4~6 (중간)', '7 이상 (심함)']);
    session.painLevel = ['없음', '1~3', '4~6', '7+'][n];
  }

  if (!session.condition) {
    const n = await choose('오늘 전체 컨디션은?', ['최고 💫', '좋음 🙂', '보통 😐', '나쁨 😔', '매우 나쁨 😢']);
    session.condition = ['최고', '좋음', '보통', '나쁨', '매우 나쁨'][n];
  }

  if (!session.mood) {
    const n = await choose('오늘 기분은 어때요?', ['😄 행복', '🙂 괜찮음', '😐 그저 그럼', '😔 우울', '😢 힘듦']);
    session.mood = ['😄 행복', '🙂 괜찮음', '😐 그저 그럼', '😔 우울', '😢 힘듦'][n];
  }

  console.log('\n오늘 잘된 점을 메모하고 싶으면 입력해주세요. (건너뛰려면 Enter)');
  const memoInput = (await ask('> ')).trim();
  session.memo = memoInput || '';

  const romScore = romToScore(session.rangeOfMotion);
  const painScore = painToScore(session.painLevel);
  const routineSummary = session.completedSteps.join(', ') || '없음';

  console.log('\n📝 Notion에 저장 중...');
  try {
    await notion.pages.create({
      parent: { database_id: REHAB_DB },
      properties: {
        Name: { title: [{ text: { content: `재활 ${session.date}` } }] },
        날짜: { date: { start: session.date } },
        '오늘 한 재활 운동': { rich_text: [{ text: { content: routineSummary } }] },
        컨디션: { select: { name: session.condition } },
        기분: { select: { name: session.mood } },
        '통증 수준 (0~10)': { number: painScore },
        '왼팔 움직임 (0~10)': { number: romScore },
        '나아진 점 / 메모': { rich_text: [{ text: { content: session.memo } }] },
      },
    });
    console.log('✅ Notion 저장 완료!');
  } catch (err) {
    console.log(`⚠️ Notion 저장 실패: ${err.message}`);
    console.log('아래 기록을 따로 메모해두세요:');
    console.log(`  날짜: ${session.date}`);
    console.log(`  운동: ${routineSummary}`);
    console.log(`  가동범위: ${session.rangeOfMotion} (${romScore}/10)`);
    console.log(`  통증: ${session.painLevel} (${painScore}/10)`);
    console.log(`  컨디션: ${session.condition}`);
  }

  console.log(`
✅ 오늘 재활 기록 완료!

💪 왼팔 가동범위: ${session.rangeOfMotion} (${romScore}/10)
😊 컨디션: ${session.condition}
💭 기분: ${session.mood}
🗓 날짜: ${session.date}
📋 완료 운동: ${routineSummary}

5년째 꾸준히 하고 있는 선영님,
오늘도 정말 대단해요! 🎉
조금씩 나아지고 있어요 💙
`);

  rl.close();
}

// ─── 트렌드 보기 ─────────────────────────────────────────────────────────────

async function viewTrends() {
  console.log('\n📊 최근 7일 재활 기록 조회 중...');

  const fromDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000 + 9 * 60 * 60 * 1000)
    .toISOString().slice(0, 10);

  try {
    const res = await notion.databases.query({
      database_id: REHAB_DB,
      filter: { property: '날짜', date: { on_or_after: fromDate } },
      sorts: [{ property: '날짜', direction: 'ascending' }],
      page_size: 10,
    });

    if (res.results.length === 0) {
      console.log('최근 7일 기록이 없어요. 재활을 시작해볼까요? 💙');
      rl.close();
      return;
    }

    const records = res.results.map(p => ({
      date: p.properties['날짜']?.date?.start || '?',
      rom: p.properties['왼팔 움직임 (0~10)']?.number ?? null,
      pain: p.properties['통증 수준 (0~10)']?.number ?? null,
      condition: p.properties['컨디션']?.select?.name || '?',
    }));

    const withRom = records.filter(r => r.rom !== null);
    const withPain = records.filter(r => r.pain !== null);
    const avgRom = withRom.length ? withRom.reduce((s, r) => s + r.rom, 0) / withRom.length : 0;
    const avgPain = withPain.length ? withPain.reduce((s, r) => s + r.pain, 0) / withPain.length : 0;

    console.log(`\n이번 주 왼팔 평균 가동범위: ${avgRom.toFixed(1)}/10 📈`);
    console.log(`평균 통증 수준: ${avgPain.toFixed(1)}/10`);
    console.log('\n날짜별 기록:');
    for (const r of records) {
      const bar = '█'.repeat(Math.round(r.rom ?? 0));
      console.log(`  ${r.date}: 움직임 ${r.rom ?? '?'}/10 [${bar.padEnd(10)}] | 통증 ${r.pain ?? '?'}/10 | ${r.condition}`);
    }

    if (avgRom >= 8) console.log('\n정말 잘 하고 있어요! 대단해요 💙🎉');
    else if (avgRom >= 6) console.log('\n꾸준히 나아지고 있어요! 조금씩이면 충분해요 💙');
    else console.log('\n오늘도 포기하지 않은 선영님, 그것만으로 대단해요 💙');
  } catch (err) {
    console.log(`⚠️ 기록 조회 실패: ${err.message}`);
  }

  rl.close();
}

// ─── 재활 시작 (모드 1) ──────────────────────────────────────────────────────

async function startRehab() {
  console.log('\n💪 왼팔 재활 도우미 시작!\n');

  const condIdx = await choose('오늘 컨디션 어때요? 😊', ['😊 좋아요 (좋음)', '😐 보통이에요 (보통)', '😔 별로예요 (나쁨)']);
  session.condition = ['좋음', '보통', '나쁨'][condIdx];

  const painIdx = await choose('왼팔 쪽에 지금 통증 있어요?', ['없어요', '살짝 있어요', '좀 있어요']);
  if (painIdx === 2) {
    console.log('\n⚠️ 통증이 있을 때는 무리하지 않는 게 중요해요!');
    const actionIdx = await choose('어떻게 할까요?', ['가벼운 루틴만 할게요', '오늘은 쉴게요', '그래도 기본 루틴 할게요']);
    if (actionIdx === 1) {
      console.log('\n💙 오늘은 푹 쉬어요! 쉬는 것도 재활이에요.\n');
      rl.close();
      return;
    }
    if (actionIdx === 0) { await lightRoutine(); return; }
  }

  if (condIdx === 0) {
    console.log('\n✨ 컨디션이 좋네요! 전체 루틴(5단계)으로 가볼까요?');
    await fullRoutine();
  } else if (condIdx === 1) {
    console.log('\n😊 기본 루틴(3단계)으로 진행할게요!');
    await basicRoutine();
  } else {
    console.log('\n💙 오늘은 짧게 해요. 가벼운 루틴(2단계)으로 할게요!');
    await lightRoutine();
  }
}

// ─── 메인 ────────────────────────────────────────────────────────────────────

async function main() {
  const arg = process.argv[2];

  if (arg === 'trends') {
    await viewTrends();
    return;
  }

  console.log('\n🦾 선영님 왼팔 재활 도우미');
  console.log('================================\n');

  const n = await choose('무엇을 도와드릴까요?', [
    '재활 시작하기 💪',
    '기본 루틴 바로 시작 (3단계)',
    '전체 루틴 바로 시작 (5단계)',
    '최근 재활 기록 보기 📊',
    '종료',
  ]);

  if (n === 0) await startRehab();
  else if (n === 1) await basicRoutine();
  else if (n === 2) await fullRoutine();
  else if (n === 3) await viewTrends();
  else {
    console.log('\n오늘도 수고하셨어요! 💙\n');
    rl.close();
  }
}

main().catch(err => {
  console.error('[오류]', err.message);
  rl.close();
  process.exit(1);
});

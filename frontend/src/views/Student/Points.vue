<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from '@/ui/feedback'
import { useRoute, useRouter } from 'vue-router'
import QRCode from 'qrcode'
import { fetchStudentChallengePoints, fetchStudentDashboard } from '../../api/services/student.js'
import { studentCheckIn } from '../../api/services/questionBank.js'
import { useSubjectContextStore } from '../../stores/subjectContextStore.js'
import { buildContentLabelMaps } from '../../utils/contentBaseline.js'
import {
  buildStudentPracticeRouteLocation,
  STUDENT_PRACTICE_MODULE,
  STUDENT_PRACTICE_SOURCE,
} from '../../utils/studentPracticeNavigation.js'
import {
  buildStudentRouteLocationForSubject,
  normalizeStudentSubjectOptions,
} from '../../utils/studentSubjectContext.js'

const route = useRoute()
const router = useRouter()
const subjectContextStore = useSubjectContextStore()

const SUBJECT_CODE_LABELS = {
  POLITICS: '政治',
  ENGLISH: '英语',
  ADVANCED_MATH_1: '高等数学（一）',
  ADVANCED_MATH_2: '高等数学（二）',
  INFO_TECH_INTRO: '信息技术概论',
}

function svgToDataUri(svg) {
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg.replace(/\s+/g, ' ').trim())}`
}

function buildLevelArtSvg(level) {
  const stars = Array.from({ length: level.starCount }, (_item, index) => {
    const x = 138 + (index * 40)
    return `
      <g transform="translate(${x} 78)">
        <circle cx="0" cy="0" r="16" fill="${level.starGlow}" opacity="0.18" />
        <path d="M0-13 L4.3-4.6 L13-3.8 L6.5 2.5 L8.5 11 L0 6.2 L-8.5 11 L-6.5 2.5 L-13 -3.8 L-4.3 -4.6 Z" fill="${level.starFill}" />
      </g>
    `
  }).join('')

  return `
    <svg width="420" height="360" viewBox="0 0 420 360" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="panel-${level.code}" x1="40" y1="32" x2="378" y2="330" gradientUnits="userSpaceOnUse">
          <stop stop-color="${level.accentFrom}" />
          <stop offset="1" stop-color="${level.accentTo}" />
        </linearGradient>
        <linearGradient id="crest-${level.code}" x1="140" y1="102" x2="280" y2="260" gradientUnits="userSpaceOnUse">
          <stop stop-color="${level.badgeFrom}" />
          <stop offset="1" stop-color="${level.badgeTo}" />
        </linearGradient>
      </defs>
      <rect x="28" y="22" width="364" height="316" rx="36" fill="url(#panel-${level.code})" />
      <circle cx="332" cy="78" r="46" fill="${level.orbitColor}" opacity="0.22" />
      <circle cx="102" cy="292" r="62" fill="${level.orbitColor}" opacity="0.16" />
      ${stars}
      <path d="M210 98 C246 98 278 116 292 144 V210 C292 246 264 280 210 304 C156 280 128 246 128 210 V144 C142 116 174 98 210 98 Z" fill="url(#crest-${level.code})" />
      <path d="M210 118 C236 118 260 130 272 152 V205 C272 232 248 254 210 276 C172 254 148 232 148 205 V152 C160 130 184 118 210 118 Z" fill="rgba(255,255,255,0.2)" />
      <circle cx="210" cy="168" r="40" fill="rgba(255,255,255,0.92)" />
      <path d="M188 201 C198 190 222 190 232 201" stroke="rgba(255,255,255,0.92)" stroke-width="12" stroke-linecap="round" />
      <path d="M186 167 C190 155 201 148 210 148 C219 148 230 155 234 167" stroke="${level.faceStroke}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" />
      <circle cx="195" cy="166" r="6" fill="${level.faceStroke}" />
      <circle cx="225" cy="166" r="6" fill="${level.faceStroke}" />
      <path d="M177 238 H243" stroke="rgba(255,255,255,0.68)" stroke-width="10" stroke-linecap="round" />
      <rect x="146" y="248" width="128" height="20" rx="10" fill="rgba(255,255,255,0.24)" />
      <text x="210" y="317" text-anchor="middle" font-size="30" font-weight="800" fill="rgba(255,255,255,0.96)" font-family="'PingFang SC','Microsoft YaHei',sans-serif">${level.shortName}</text>
    </svg>
  `
}

const LEVEL_RULES = [
  {
    code: 'BRONZE',
    name: '刷题青铜',
    shortName: '青铜',
    min: 0,
    max: 199,
    cue: '先把会做的题稳定做对，建立每天都能涨分的手感。',
    cheer: '先稳住基础盘，今天每一道对题都在帮你把升本节奏拉顺。',
    accentFrom: 'rgb(217, 119, 6)',
    accentTo: 'rgb(246, 173, 85)',
    badgeFrom: 'rgb(245, 158, 11)',
    badgeTo: 'rgb(180, 83, 9)',
    faceStroke: 'rgb(138, 74, 8)',
    orbitColor: 'rgb(253, 230, 138)',
    starFill: 'rgb(255, 241, 194)',
    starGlow: 'rgb(255, 246, 220)',
    cardGlow: 'rgba(217, 119, 6, 0.18)',
    chipBg: 'rgba(255, 247, 237, 0.92)',
    chipText: 'rgb(154, 52, 18)',
    qrDark: 'rgb(138, 74, 8)',
    starCount: 1,
  },
  {
    code: 'SILVER',
    name: '刷题白银',
    shortName: '白银',
    min: 200,
    max: 499,
    cue: '开始形成连续正确输出，刷题不再只靠运气。',
    cheer: '正确率开始连起来了，把这股稳定劲继续往上推。',
    accentFrom: 'rgb(148, 163, 184)',
    accentTo: 'rgb(226, 232, 240)',
    badgeFrom: 'rgb(203, 213, 225)',
    badgeTo: 'rgb(100, 116, 139)',
    faceStroke: 'rgb(71, 85, 105)',
    orbitColor: 'rgb(248, 250, 252)',
    starFill: 'rgb(255, 255, 255)',
    starGlow: 'rgb(248, 250, 252)',
    cardGlow: 'rgba(148, 163, 184, 0.18)',
    chipBg: 'rgba(248, 250, 252, 0.96)',
    chipText: 'rgb(51, 65, 85)',
    qrDark: 'rgb(71, 85, 105)',
    starCount: 2,
  },
  {
    code: 'GOLD',
    name: '刷题黄金',
    shortName: '黄金',
    min: 500,
    max: 899,
    cue: '基础题和常规题逐步稳住，提分效率开始拉开差距。',
    cheer: '开始进入会做且能拿分的阶段，今天很适合再冲一轮。',
    accentFrom: 'rgb(245, 158, 11)',
    accentTo: 'rgb(252, 211, 77)',
    badgeFrom: 'rgb(251, 191, 36)',
    badgeTo: 'rgb(180, 83, 9)',
    faceStroke: 'rgb(133, 77, 14)',
    orbitColor: 'rgb(254, 243, 199)',
    starFill: 'rgb(255, 251, 234)',
    starGlow: 'rgb(255, 247, 204)',
    cardGlow: 'rgba(245, 158, 11, 0.18)',
    chipBg: 'rgba(255, 251, 235, 0.96)',
    chipText: 'rgb(146, 64, 14)',
    qrDark: 'rgb(133, 77, 14)',
    starCount: 3,
  },
  {
    code: 'PLATINUM',
    name: '刷题铂金',
    shortName: '铂金',
    min: 900,
    max: 1399,
    cue: '知识点连接更顺，做题速度和正确率开始一起往上走。',
    cheer: '你已经不只是会做，正在把方法和速度一起练成自己的优势。',
    accentFrom: 'rgb(15, 118, 110)',
    accentTo: 'rgb(94, 234, 212)',
    badgeFrom: 'rgb(45, 212, 191)',
    badgeTo: 'rgb(17, 94, 89)',
    faceStroke: 'rgb(19, 78, 74)',
    orbitColor: 'rgb(204, 251, 241)',
    starFill: 'rgb(236, 254, 255)',
    starGlow: 'rgb(230, 255, 251)',
    cardGlow: 'rgba(15, 118, 110, 0.18)',
    chipBg: 'rgba(240, 253, 250, 0.96)',
    chipText: 'rgb(17, 94, 89)',
    qrDark: 'rgb(19, 78, 74)',
    starCount: 4,
  },
  {
    code: 'DIAMOND',
    name: '刷题钻石',
    shortName: '钻石',
    min: 1400,
    max: 1999,
    cue: '薄弱项正在被持续回补，考场上更容易守住基本盘。',
    cheer: '这时候的坚持最值钱，你正在把薄弱点一块一块补成稳分点。',
    accentFrom: 'rgb(37, 99, 235)',
    accentTo: 'rgb(147, 197, 253)',
    badgeFrom: 'rgb(96, 165, 250)',
    badgeTo: 'rgb(29, 78, 216)',
    faceStroke: 'rgb(30, 58, 138)',
    orbitColor: 'rgb(219, 234, 254)',
    starFill: 'rgb(239, 246, 255)',
    starGlow: 'rgb(219, 234, 254)',
    cardGlow: 'rgba(37, 99, 235, 0.18)',
    chipBg: 'rgba(239, 246, 255, 0.96)',
    chipText: 'rgb(29, 78, 216)',
    qrDark: 'rgb(30, 58, 138)',
    starCount: 5,
  },
  {
    code: 'STAR',
    name: '刷题星耀',
    shortName: '星耀',
    min: 2000,
    max: 2999,
    cue: '进入冲刺区，说明你已经把大量得分点练成了稳定输出。',
    cheer: '你已经接近冲线节奏，继续拉高密度，就是在给成绩单做准备。',
    accentFrom: 'rgb(124, 58, 237)',
    accentTo: 'rgb(196, 181, 253)',
    badgeFrom: 'rgb(139, 92, 246)',
    badgeTo: 'rgb(91, 33, 182)',
    faceStroke: 'rgb(76, 29, 149)',
    orbitColor: 'rgb(237, 233, 254)',
    starFill: 'rgb(245, 243, 255)',
    starGlow: 'rgb(237, 233, 254)',
    cardGlow: 'rgba(124, 58, 237, 0.18)',
    chipBg: 'rgba(245, 243, 255, 0.96)',
    chipText: 'rgb(109, 40, 217)',
    qrDark: 'rgb(76, 29, 149)',
    starCount: 6,
  },
  {
    code: 'KING',
    name: '刷题王者',
    shortName: '王者',
    min: 3000,
    max: 3000,
    cue: '高频正确已经沉淀成实力，离升本冲线只差临场发挥。',
    cheer: '你已经把稳定正确练成实力，现在要做的是把实力稳稳带进考场。',
    accentFrom: 'rgb(190, 18, 60)',
    accentTo: 'rgb(251, 113, 133)',
    badgeFrom: 'rgb(244, 63, 94)',
    badgeTo: 'rgb(159, 18, 57)',
    faceStroke: 'rgb(136, 19, 55)',
    orbitColor: 'rgb(255, 228, 230)',
    starFill: 'rgb(255, 241, 242)',
    starGlow: 'rgb(255, 228, 230)',
    cardGlow: 'rgba(190, 18, 60, 0.18)',
    chipBg: 'rgba(255, 241, 242, 0.96)',
    chipText: 'rgb(190, 18, 60)',
    qrDark: 'rgb(136, 19, 55)',
    starCount: 7,
  },
].map((level) => ({
  ...level,
  image: svgToDataUri(buildLevelArtSvg(level)),
}))

const loading = ref(false)
const checkInSubmitting = ref(false)
const dashboardPayload = ref({})
const boostQrCodeDataUrl = ref('')
const summary = ref({
  subjectCode: '',
  total: 0,
  todayDelta: 0,
  correctSubmitCount: 0,
  todayCorrectSubmitCount: 0,
  rank: 0,
  leaderboard: [],
  awardUnlocked: false,
  awardProgress: 0,
  awardThreshold: 3000,
  award: {},
  scoreCap: 3000,
  cappedTotal: 0,
  scorePercent: 0,
  levelCode: 'BRONZE',
  levelName: '刷题青铜',
  levelFloor: 0,
  levelCeil: 199,
  levelProgress: 0,
  levelProgressTotal: 200,
  levelProgressPercent: 0,
  nextLevelCode: 'SILVER',
  nextLevelName: '刷题白银',
  nextLevelThreshold: 200,
  pointsToNextLevel: 200,
  isTopLevel: false,
})

function toText(value) {
  return String(value || '').trim()
}

function resolveSubjectDisplayName(subjectCode, subjectName = '') {
  const normalizedSubjectName = toText(subjectName)
  if (normalizedSubjectName && normalizedSubjectName !== toText(subjectCode)) {
    return normalizedSubjectName
  }
  const normalizedSubjectCode = toText(subjectCode)
  return SUBJECT_CODE_LABELS[normalizedSubjectCode] || normalizedSubjectName || normalizedSubjectCode || '当前科目'
}

function drawRoundedRect(ctx, x, y, width, height, radius, fillStyle, strokeStyle = '', lineWidth = 1) {
  const limitedRadius = Math.min(radius, width / 2, height / 2)
  ctx.save()
  ctx.beginPath()
  ctx.moveTo(x + limitedRadius, y)
  ctx.arcTo(x + width, y, x + width, y + height, limitedRadius)
  ctx.arcTo(x + width, y + height, x, y + height, limitedRadius)
  ctx.arcTo(x, y + height, x, y, limitedRadius)
  ctx.arcTo(x, y, x + width, y, limitedRadius)
  ctx.closePath()
  if (fillStyle) {
    ctx.fillStyle = fillStyle
    ctx.fill()
  }
  if (strokeStyle) {
    ctx.strokeStyle = strokeStyle
    ctx.lineWidth = lineWidth
    ctx.stroke()
  }
  ctx.restore()
}

function drawWrappedText(ctx, text, x, y, maxWidth, lineHeight, maxLines = 3) {
  const words = Array.from(String(text || ''))
  let line = ''
  let currentY = y
  let lineCount = 0

  for (let index = 0; index < words.length; index += 1) {
    const testLine = `${line}${words[index]}`
    if (ctx.measureText(testLine).width > maxWidth && line) {
      ctx.fillText(line, x, currentY)
      line = words[index]
      currentY += lineHeight
      lineCount += 1
      if (lineCount >= maxLines - 1) {
        const rest = words.slice(index).join('')
        const clipped = `${line}${rest}`.slice(0, Math.max(0, Math.floor(maxWidth / 15) - 1))
        ctx.fillText(`${clipped}…`, x, currentY)
        return currentY
      }
    } else {
      line = testLine
    }
  }

  if (line) {
    ctx.fillText(line, x, currentY)
  }
  return currentY
}

function loadCanvasImage(src) {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = reject
    image.src = src
  })
}

const dashboardSubjectOptions = computed(() => {
  const { subjectNameMap } = buildContentLabelMaps({
    availableExamCategories: dashboardPayload.value?.availableExamCategories,
  })
  return normalizeStudentSubjectOptions(dashboardPayload.value)
    .map((item) => ({
      ...item,
      subjectCode: toText(item?.subjectCode),
      subjectName: resolveSubjectDisplayName(
        item?.subjectCode,
        toText(item?.subjectName) || toText(subjectNameMap.get(item?.subjectCode)),
      ),
    }))
    .filter((item) => item.subjectCode)
})

const subjectOptions = computed(() => {
  const storeRows = Array.isArray(subjectContextStore.subjectOptions) ? subjectContextStore.subjectOptions : []
  const sourceRows = storeRows.length ? storeRows : dashboardSubjectOptions.value
  return sourceRows
    .map((item) => ({
      ...item,
      subjectCode: toText(item?.subjectCode),
      subjectName: resolveSubjectDisplayName(item?.subjectCode, item?.subjectName),
    }))
    .filter((item) => item.subjectCode)
})

const selectedSubjectCode = computed(() => {
  const requestedSubjectCode = toText(route.query.subjectCode || subjectContextStore.currentSubjectCode || summary.value?.subjectCode)
  if (requestedSubjectCode && subjectOptions.value.some((item) => item.subjectCode === requestedSubjectCode)) {
    return requestedSubjectCode
  }
  return toText(subjectContextStore.currentSubjectCode || summary.value?.subjectCode || subjectOptions.value[0]?.subjectCode)
})

const selectedSubjectName = computed(() =>
  resolveSubjectDisplayName(
    selectedSubjectCode.value,
    subjectOptions.value.find((item) => item.subjectCode === selectedSubjectCode.value)?.subjectName,
  ),
)

const leaderboardRows = computed(() => (
  Array.isArray(summary.value?.leaderboard) ? summary.value.leaderboard : []
))

const scoreCap = computed(() => Number(summary.value?.scoreCap || summary.value?.awardThreshold || 3000))
const cappedTotal = computed(() =>
  Number(summary.value?.cappedTotal || Math.min(Number(summary.value?.total || 0), scoreCap.value)),
)
const scorePercent = computed(() => {
  if (Number(summary.value?.scorePercent || 0) > 0 || cappedTotal.value <= 0) {
    return Math.max(0, Math.min(100, Number(summary.value?.scorePercent || 0)))
  }
  if (!scoreCap.value) {
    return 0
  }
  return Math.max(0, Math.min(100, Math.round((cappedTotal.value / scoreCap.value) * 100)))
})
const currentLevelName = computed(() => toText(summary.value?.levelName) || '刷题青铜')
const nextLevelName = computed(() => toText(summary.value?.nextLevelName))
const nextLevelThreshold = computed(() => Number(summary.value?.nextLevelThreshold || scoreCap.value))
const pointsToNextLevel = computed(() => Number(summary.value?.pointsToNextLevel || 0))
const correctSubmitCount = computed(() => Number(summary.value?.correctSubmitCount || summary.value?.total || 0))
const todayCorrectSubmitCount = computed(() => Number(summary.value?.todayCorrectSubmitCount || summary.value?.todayDelta || 0))
const todayDelta = computed(() => Number(summary.value?.todayDelta || 0))
const currentLevelFloor = computed(() => Number(summary.value?.levelFloor || 0))
const currentLevelCeil = computed(() => Number(summary.value?.levelCeil || 0))
const checkInDone = computed(() => Boolean(dashboardPayload.value?.studentState?.checkInDone))
const streakDays = computed(() =>
  Number(dashboardPayload.value?.studentState?.streakDays || dashboardPayload.value?.streakDays || 0),
)
const isBoostEntry = computed(() => ['1', 'true', 'boost'].includes(String(route.query.boost || '').trim().toLowerCase()))

const currentLevelTheme = computed(() => {
  const levelCode = toText(summary.value?.levelCode)
  return LEVEL_RULES.find((item) => item.code === levelCode)
    || LEVEL_RULES.find((item) => item.name === currentLevelName.value)
    || LEVEL_RULES.find((item) => cappedTotal.value >= item.min && cappedTotal.value <= item.max)
    || LEVEL_RULES[0]
})

const levelProgressCopy = computed(() => (
  nextLevelName.value
    ? `再积 ${pointsToNextLevel.value} 分晋级 ${nextLevelName.value}`
    : `已达到 ${scoreCap.value} 分最高段位`
))

const heroSummaryCopy = computed(() => {
  if (nextLevelName.value) {
    return `你现在不是在盲刷，而是在把“会做”练成“考场上稳稳拿分”。再积 ${pointsToNextLevel.value} 分，就能从「${currentLevelName.value}」冲到「${nextLevelName.value}」，今天这轮练习就是给自己升本结果加码的一步。`
  }
  return '你已经来到当前科目的最高段位，说明这门课的稳定正确输出已经练出来了。接下来更重要的是继续保持这股势头，把高段位真正带到考场上。'
})

const currentLevelWindowCopy = computed(() => {
  if (nextLevelName.value) {
    return `${currentLevelName.value} 当前区间 ${currentLevelFloor.value}-${currentLevelCeil.value} 分，冲到 ${nextLevelThreshold.value} 分即可晋级 ${nextLevelName.value}。`
  }
  return `${currentLevelName.value} 是当前封顶段位，达到 ${scoreCap.value} 分后进入满阶状态。`
})

const levelMilestones = computed(() => LEVEL_RULES.map((item) => ({
  ...item,
  rangeLabel: item.min === item.max ? `${item.min} 分` : `${item.min}-${item.max} 分`,
  reached: cappedTotal.value >= item.min,
  active: item.code === currentLevelTheme.value.code,
})))

const progressActionCopy = computed(() => {
  if (nextLevelName.value) {
    return `下一步先补齐 ${pointsToNextLevel.value} 分差距，把当前科目推到 ${nextLevelName.value}。每多一轮稳定输出，排名、心态和做题手感都会更稳。`
  }
  return '当前已经到达封顶段位，接下来就继续保持训练密度，把高段位的正确率固化成考场上的稳定发挥。'
})

const momentumCopy = computed(() => {
  if (todayDelta.value > 0) {
    return `今天已经拿到 ${todayDelta.value} 分，你不是在“想提分”，而是在把提分动作一分一分做出来。`
  }
  return '今天还没开始涨分也没关系，先拿下第一笔有效积分，状态就会重新往前走。'
})

const successConnectionItems = computed(() => ([
  {
    title: '积分记录的是有效正确输出',
    description: `累计答对 ${correctSubmitCount.value} 题次，代表你已经完成了 ${correctSubmitCount.value} 次“会做并且做对”的训练。真正决定升本分数的，是这种能稳定把分拿到手的输出。`,
  },
  {
    title: '段位体现的是持续稳定性',
    description: nextLevelName.value
      ? `${currentLevelName.value} 往上，每次晋级都要求更长时间保持正确率。你现在离 ${nextLevelName.value} 还差 ${pointsToNextLevel.value} 分，跨过去就意味着你的练习节奏、耐心和稳定性又往前推了一层。`
      : '你已经来到最高段位，说明这门科目不是偶尔刷出好成绩，而是已经形成了足够密度的稳定训练。真正能决定结果的，往往就是这种稳定性。',
  },
  {
    title: '手机打卡是在给自己续上节奏',
    description: checkInDone.value
      ? `今天的打卡已经完成，连续备考 ${streakDays.value} 天。把这份节奏保持住，练习积分和真实成绩往往会一起往上走。`
      : '打卡不是形式，它是在提醒你“今天这趟已经开起来了”。扫一下码、给自己加一笔积分，再去刷题，会更容易把状态拉起来。',
  },
]))

const heroTagList = computed(() => ([
  '答对 1 题 = 1 段位分',
  currentLevelTheme.value.shortName ? `${currentLevelTheme.value.shortName}段位形象已点亮` : '当前段位形象已点亮',
  checkInDone.value ? `连续备考 ${streakDays.value} 天` : '扫码可在手机上打卡助力',
]))

const shareCopy = computed(() => {
  const rankText = summary.value?.rank ? `同科目排名 #${summary.value.rank}` : '继续冲榜中'
  if (nextLevelName.value) {
    return `${selectedSubjectName.value}我已经来到「${currentLevelName.value}」，当前段位分 ${Number(summary.value?.total || 0)}，${rankText}，再积 ${pointsToNextLevel.value} 分就能升到「${nextLevelName.value}」。今天继续给自己打卡助力，把会做的题练成升本考场上稳稳拿下的分。`
  }
  return `${selectedSubjectName.value}我已经把段位练到「${currentLevelName.value}」，当前段位分 ${Number(summary.value?.total || 0)}，${rankText}。接下来继续稳住节奏，把高段位真正练成升本时的稳定发挥。`
})

const boostBannerCopy = computed(() => {
  if (checkInDone.value) {
    return '今天的打卡积分已经拿下了。现在继续刷题、分享海报，把这股向上的劲保持到晚上。'
  }
  return '你已经从二维码进入手机助力入口，点一下就能完成今日打卡，让积分、状态和节奏一起接上。'
})

const sharePanelCopy = computed(() => {
  if (checkInDone.value) {
    return '今天已经打卡完成，二维码现在更适合转给手机端保存海报、回看段位和提醒自己继续练。'
  }
  if (isBoostEntry.value) {
    return '手机助力模式已开启，先打一针行动力，再把这股节奏带回今天的刷题主线。'
  }
  return '下载海报旁边这张二维码可以直接扫到手机上，用打卡把今天的状态拉起来，也方便把练习成果发给自己继续加油。'
})

const assistActionLabel = computed(() => (checkInDone.value ? '今日已打卡' : '一键打卡助力'))

const assistEntryUrl = computed(() => {
  if (typeof window === 'undefined') {
    return ''
  }
  const resolved = router.resolve({
    path: '/student/analysis/points',
    query: {
      subjectCode: selectedSubjectCode.value,
      boost: '1',
    },
  })
  return new URL(resolved.href, window.location.origin).toString()
})

const currentLevelStyle = computed(() => ({
  '--points-rank-from': currentLevelTheme.value.accentFrom,
  '--points-rank-to': currentLevelTheme.value.accentTo,
  '--points-rank-glow': currentLevelTheme.value.cardGlow,
  '--points-rank-chip-bg': currentLevelTheme.value.chipBg,
  '--points-rank-chip-text': currentLevelTheme.value.chipText,
}))

async function renderBoostQrCode() {
  if (!assistEntryUrl.value) {
    boostQrCodeDataUrl.value = ''
    return
  }
  try {
    boostQrCodeDataUrl.value = await QRCode.toDataURL(assistEntryUrl.value, {
      margin: 1,
      width: 320,
      color: {
        dark: currentLevelTheme.value.qrDark,
        light: 'rgba(255, 255, 255, 0)',
      },
    })
  } catch (_error) {
    boostQrCodeDataUrl.value = ''
  }
}

async function loadDashboard() {
  dashboardPayload.value = await fetchStudentDashboard()
  const preferredSubjectCode = toText(route.query.subjectCode || subjectContextStore.currentSubjectCode || summary.value?.subjectCode)
  const normalizedOptions = dashboardSubjectOptions.value
  if (normalizedOptions.length) {
    subjectContextStore.setSubjectOptions(normalizedOptions, preferredSubjectCode)
    return
  }
  if (!subjectContextStore.subjectOptions.length) {
    await subjectContextStore.ensureStudentSubjectContext()
  }
}

async function loadSummary(subjectCode = '') {
  const normalizedSubjectCode = toText(subjectCode || selectedSubjectCode.value || subjectOptions.value[0]?.subjectCode)
  if (!normalizedSubjectCode) {
    return
  }
  loading.value = true
  try {
    summary.value = await fetchStudentChallengePoints({ subjectCode: normalizedSubjectCode })
  } finally {
    loading.value = false
  }
}

async function handleSubjectChange(nextSubjectCode) {
  const normalizedSubjectCode = toText(nextSubjectCode)
  if (!normalizedSubjectCode) {
    return
  }
  subjectContextStore.setCurrentSubjectCode(normalizedSubjectCode)
  const subjectMeta = subjectOptions.value.find((item) => item.subjectCode === normalizedSubjectCode)
    || subjectContextStore.subjectMetaMap[normalizedSubjectCode]
    || {}
  await router.replace(buildStudentRouteLocationForSubject(
    route,
    normalizedSubjectCode,
    toText(subjectMeta?.subjectId),
  ))
}

async function navigateToModule(module) {
  await router.push(buildStudentPracticeRouteLocation({
    module,
    subjectCode: selectedSubjectCode.value,
    practiceSource: STUDENT_PRACTICE_SOURCE.POINTS,
    practiceSourceLabel: '积分页进入',
  }))
}

async function handleShare() {
  const payload = `${shareCopy.value}\n${assistEntryUrl.value}`
  if (navigator.share) {
    try {
      await navigator.share({
        title: '练习积分打卡助力',
        text: shareCopy.value,
        url: assistEntryUrl.value,
      })
      return
    } catch (_error) {
      // Fall through to clipboard.
    }
  }
  try {
    await navigator.clipboard.writeText(payload)
    ElMessage.success('分享文案和助力链接已复制，可直接发送。')
  } catch (_error) {
    ElMessage.warning('当前环境不支持直接分享，请手动复制内容。')
  }
}

async function handleCopyBoostLink() {
  try {
    await navigator.clipboard.writeText(assistEntryUrl.value)
    ElMessage.success('助力链接已复制，发给手机端就能继续打卡。')
  } catch (_error) {
    ElMessage.warning('当前环境不支持复制，请手动复制当前地址。')
  }
}

async function handleSupportCheckIn() {
  if (checkInDone.value || checkInSubmitting.value) {
    if (checkInDone.value) {
      ElMessage.success('今日已经打卡完成啦。')
    }
    return
  }
  checkInSubmitting.value = true
  try {
    const response = await studentCheckIn()
    const data = response?.data && typeof response.data === 'object' ? response.data : response || {}
    ElMessage.success(`打卡成功，当前积分 ${Number(data?.points || 0)}，连续打卡 ${Number(data?.streakDays || 0)} 天。`)
    await Promise.all([
      loadDashboard(),
      loadSummary(selectedSubjectCode.value),
    ])
  } catch (error) {
    ElMessage.error(String(error?.response?.data?.message || error?.message || '打卡失败'))
  } finally {
    checkInSubmitting.value = false
  }
}

async function buildPosterCanvas() {
  const canvas = document.createElement('canvas')
  canvas.width = 1240
  canvas.height = 1680
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    return null
  }

  const levelTheme = currentLevelTheme.value
  const qrCodeDataUrl = boostQrCodeDataUrl.value || await QRCode.toDataURL(assistEntryUrl.value, {
    margin: 1,
    width: 320,
    color: {
      dark: levelTheme.qrDark,
      light: 'rgba(255, 255, 255, 0)',
    },
  })

  const backgroundGradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height)
  backgroundGradient.addColorStop(0, 'rgb(239, 246, 255)')
  backgroundGradient.addColorStop(1, 'rgb(255, 247, 237)')
  ctx.fillStyle = backgroundGradient
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  ctx.fillStyle = 'rgba(255,255,255,0.5)'
  ctx.beginPath()
  ctx.arc(1080, 140, 150, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.arc(140, 1480, 220, 0, Math.PI * 2)
  ctx.fill()

  const heroGradient = ctx.createLinearGradient(80, 80, 1160, 620)
  heroGradient.addColorStop(0, levelTheme.accentFrom)
  heroGradient.addColorStop(1, levelTheme.accentTo)
  drawRoundedRect(ctx, 72, 72, 1096, 590, 42, heroGradient)

  ctx.fillStyle = 'rgba(255,255,255,0.95)'
  ctx.font = '800 46px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText('今天也在为升本加码', 126, 156)
  ctx.font = '700 66px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText(selectedSubjectName.value, 126, 246)
  ctx.font = '800 58px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText(currentLevelName.value, 126, 332)
  ctx.font = '500 30px "PingFang SC","Microsoft YaHei",sans-serif'
  drawWrappedText(ctx, heroSummaryCopy.value, 126, 390, 570, 44, 3)

  drawRoundedRect(ctx, 126, 500, 214, 104, 24, 'rgba(255,255,255,0.16)', 'rgba(255,255,255,0.28)')
  drawRoundedRect(ctx, 362, 500, 214, 104, 24, 'rgba(255,255,255,0.16)', 'rgba(255,255,255,0.28)')
  drawRoundedRect(ctx, 598, 500, 214, 104, 24, 'rgba(255,255,255,0.16)', 'rgba(255,255,255,0.28)')

  ctx.font = '500 24px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText('累计段位分', 156, 542)
  ctx.fillText('今日新增', 392, 542)
  ctx.fillText('当前排名', 628, 542)
  ctx.font = '800 42px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText(String(Number(summary.value?.total || 0)), 156, 588)
  ctx.fillText(`+${todayDelta.value}`, 392, 588)
  ctx.fillText(summary.value?.rank ? `#${summary.value.rank}` : '冲榜中', 628, 588)

  const levelArt = await loadCanvasImage(levelTheme.image)
  ctx.drawImage(levelArt, 774, 118, 300, 256)

  drawRoundedRect(ctx, 792, 408, 250, 166, 28, 'rgba(255,255,255,0.16)', 'rgba(255,255,255,0.28)')
  ctx.fillStyle = 'rgba(255,255,255,0.98)'
  ctx.font = '700 28px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText('继续冲级', 826, 456)
  ctx.font = '500 26px "PingFang SC","Microsoft YaHei",sans-serif'
  drawWrappedText(ctx, levelTheme.cheer, 826, 504, 196, 38, 3)

  drawRoundedRect(ctx, 72, 724, 646, 340, 34, 'rgba(255,255,255,0.94)', 'rgba(191,219,254,0.6)')
  ctx.fillStyle = 'rgb(15, 23, 42)'
  ctx.font = '800 38px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText('手机扫码打卡助力', 118, 804)
  ctx.font = '500 26px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillStyle = 'rgb(71, 85, 105)'
  drawWrappedText(ctx, sharePanelCopy.value, 118, 856, 540, 40, 3)

  const qrImage = await loadCanvasImage(qrCodeDataUrl)
  drawRoundedRect(ctx, 118, 900, 196, 196, 26, levelTheme.chipBg)
  ctx.drawImage(qrImage, 136, 918, 160, 160)

  ctx.fillStyle = 'rgb(15, 23, 42)'
  ctx.font = '700 28px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText(checkInDone.value ? '今日节奏已接上' : '今日未打卡可直接加积分', 352, 950)
  ctx.font = '500 24px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillStyle = 'rgb(100, 116, 139)'
  drawWrappedText(ctx, checkInDone.value ? '现在更适合把海报发给自己，晚上复盘时再看一眼段位进度。' : '扫到手机后点一下打卡，再去做今天的刷题，状态会更容易往前走。', 352, 996, 300, 36, 4)

  drawRoundedRect(ctx, 760, 724, 408, 340, 34, 'rgba(255,255,255,0.94)', 'rgba(191,219,254,0.6)')
  ctx.fillStyle = 'rgb(15, 23, 42)'
  ctx.font = '800 38px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText('冲级提醒', 806, 804)
  ctx.font = '500 24px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillStyle = 'rgb(71, 85, 105)'
  drawWrappedText(ctx, progressActionCopy.value, 806, 856, 316, 38, 4)

  drawRoundedRect(ctx, 806, 938, 314, 86, 22, levelTheme.chipBg)
  ctx.fillStyle = levelTheme.chipText
  ctx.font = '700 26px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText(nextLevelName.value ? `再积 ${pointsToNextLevel.value} 分升到 ${nextLevelName.value}` : '当前已达到最高段位', 832, 990)

  drawRoundedRect(ctx, 72, 1122, 1096, 440, 34, 'rgba(255,255,255,0.94)', 'rgba(191,219,254,0.6)')
  ctx.fillStyle = 'rgb(15, 23, 42)'
  ctx.font = '800 38px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText('把势头继续带下去', 118, 1202)

  successConnectionItems.value.forEach((item, index) => {
    const y = 1252 + (index * 110)
    drawRoundedRect(ctx, 118, y - 20, 1004, 88, 22, 'rgba(248,250,252,0.96)')
    ctx.fillStyle = 'rgb(15, 23, 42)'
    ctx.font = '700 26px "PingFang SC","Microsoft YaHei",sans-serif'
    ctx.fillText(item.title, 148, y + 14)
    ctx.fillStyle = 'rgb(71, 85, 105)'
    ctx.font = '500 22px "PingFang SC","Microsoft YaHei",sans-serif'
    drawWrappedText(ctx, item.description, 148, y + 48, 942, 32, 2)
  })

  ctx.fillStyle = 'rgb(15, 23, 42)'
  ctx.font = '800 36px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText('今天刷的每一道对题，都在给升本结果加筹码。', 118, 1618)
  ctx.fillStyle = 'rgb(100, 116, 139)'
  ctx.font = '500 22px "PingFang SC","Microsoft YaHei",sans-serif'
  ctx.fillText('河北专升本 AI 学习平台 · 练习积分打卡助力海报', 118, 1652)

  return canvas
}

async function handleDownloadPoster() {
  const canvas = await buildPosterCanvas()
  if (!canvas) {
    ElMessage.error('海报生成失败，请稍后重试。')
    return
  }
  const link = document.createElement('a')
  link.href = canvas.toDataURL('image/png')
  link.download = `${selectedSubjectName.value || 'subject'}-challenge-poster.png`
  link.click()
}

function buildLevelCardStyle(level) {
  return {
    '--milestone-from': level.accentFrom,
    '--milestone-to': level.accentTo,
    '--milestone-glow': level.cardGlow,
    '--milestone-chip-bg': level.chipBg,
    '--milestone-chip-text': level.chipText,
  }
}

onMounted(async () => {
  await loadDashboard()
  if (selectedSubjectCode.value && toText(route.query.subjectCode) !== selectedSubjectCode.value) {
    const subjectMeta = subjectOptions.value.find((item) => item.subjectCode === selectedSubjectCode.value)
      || subjectContextStore.subjectMetaMap[selectedSubjectCode.value]
      || {}
    await router.replace(buildStudentRouteLocationForSubject(
      route,
      selectedSubjectCode.value,
      toText(subjectMeta?.subjectId),
    ))
  }
})

watch(
  () => selectedSubjectCode.value,
  async (nextSubjectCode, previousSubjectCode) => {
    if (!nextSubjectCode || nextSubjectCode === previousSubjectCode) {
      return
    }
    subjectContextStore.setCurrentSubjectCode(nextSubjectCode)
    await loadSummary(nextSubjectCode)
  },
  { immediate: true },
)

watch(
  [assistEntryUrl, () => currentLevelTheme.value.code],
  async () => {
    await renderBoostQrCode()
  },
  { immediate: true },
)
</script>

<template>
  <section class="points-page" v-loading="loading">
    <section v-if="isBoostEntry" class="boost-entry-banner">
      <div class="boost-entry-banner__copy">
        <span class="points-eyebrow">手机助力模式</span>
        <h4>{{ checkInDone ? '今天已经把积分领到手了' : '现在就给自己加一把劲' }}</h4>
        <p>{{ boostBannerCopy }}</p>
      </div>
      <div class="boost-entry-banner__actions">
        <el-button type="primary" :loading="checkInSubmitting" :disabled="checkInDone" @click="handleSupportCheckIn">
          {{ assistActionLabel }}
        </el-button>
        <el-button plain @click="handleShare">分享给自己</el-button>
      </div>
    </section>

    <header class="points-hero">
      <div class="points-hero__copy">
        <div class="points-hero__meta">
          <span class="points-eyebrow">练习积分</span>
          <span class="points-hero__subject-label">当前科目</span>
        </div>
        <h3>{{ selectedSubjectName }}</h3>
        <p class="points-hero__summary">{{ heroSummaryCopy }}</p>
        <div class="points-hero__stats">
          <article class="points-hero__stat-card">
            <span>累计段位分</span>
            <strong>{{ Number(summary.total || 0) }}</strong>
            <small>今日 +{{ Number(summary.todayDelta || 0) }}</small>
          </article>
          <article class="points-hero__stat-card">
            <span>累计答对题次</span>
            <strong>{{ correctSubmitCount }}</strong>
            <small>今日 +{{ todayCorrectSubmitCount }}</small>
          </article>
          <article class="points-hero__stat-card">
            <span>当前段位</span>
            <strong>{{ currentLevelName }}</strong>
            <small>{{ levelProgressCopy }}</small>
          </article>
        </div>
        <div class="points-hero__tags">
          <span v-for="item in heroTagList" :key="item" class="points-tag">{{ item }}</span>
        </div>
      </div>

      <article class="rank-showcase" :style="currentLevelStyle">
        <div class="rank-showcase__main">
          <div class="rank-showcase__image-wrap">
            <img :src="currentLevelTheme.image" :alt="`${currentLevelName}段位形象图`" class="rank-showcase__image">
          </div>
          <div class="rank-showcase__content">
            <span class="points-eyebrow">当前段位形象</span>
            <h4>{{ currentLevelName }}</h4>
            <p>{{ currentLevelTheme.cheer }}</p>
          </div>
        </div>
        <div class="rank-showcase__stats">
          <article>
            <span>累计段位分</span>
            <strong>{{ Number(summary.total || 0) }}</strong>
          </article>
          <article>
            <span>今日新增</span>
            <strong>+{{ Number(summary.todayDelta || 0) }}</strong>
          </article>
        </div>
      </article>

      <aside class="share-lab">
        <div class="share-lab__head">
          <div>
            <span class="points-eyebrow">打卡分享实验室</span>
            <h4>海报、二维码、手机助力一次配齐</h4>
          </div>
          <el-select
            :model-value="selectedSubjectCode"
            class="share-lab__subject-select"
            placeholder="切换科目"
            @change="handleSubjectChange"
          >
            <el-option
              v-for="item in subjectOptions"
              :key="item.subjectCode"
              :label="item.subjectName"
              :value="item.subjectCode"
            />
          </el-select>
        </div>
        <p class="share-lab__copy">{{ sharePanelCopy }}</p>
        <div class="share-lab__qr-card">
          <div class="share-lab__qr-frame">
            <img v-if="boostQrCodeDataUrl" :src="boostQrCodeDataUrl" alt="练习积分打卡助力二维码" class="share-lab__qr-image">
            <div v-else class="share-lab__qr-placeholder">二维码生成中</div>
          </div>
          <div class="share-lab__qr-copy">
            <strong>{{ checkInDone ? '今天已打卡，继续保持住' : '扫码到手机，先给自己助力加积分' }}</strong>
            <p>{{ checkInDone ? `已连续备考 ${streakDays} 天，接下来继续刷题，把这股势头守住。` : '扫到手机后可直接进入当前科目的积分页，一键完成今日打卡，再把海报或文案分享给自己继续提醒。' }}</p>
          </div>
        </div>
        <div class="share-lab__actions">
          <el-button type="success" plain :loading="checkInSubmitting" :disabled="checkInDone" @click="handleSupportCheckIn">
            {{ assistActionLabel }}
          </el-button>
          <el-button plain @click="handleCopyBoostLink">复制助力链接</el-button>
          <el-button plain @click="handleShare">分享文案</el-button>
          <el-button type="primary" @click="handleDownloadPoster">下载海报</el-button>
        </div>
      </aside>
    </header>

    <section class="points-story-grid">
      <article class="rules-panel">
        <div class="rules-panel__head">
          <div>
            <span class="points-eyebrow">段位地图</span>
            <h4>每个段位都有自己的形象和冲刺目标</h4>
          </div>
          <p>{{ currentLevelWindowCopy }}</p>
        </div>
        <div class="rules-grid">
          <article class="rule-card">
            <strong>1. 积分怎么来</strong>
            <p>每次有效答对记 1 分，核心是“把题做对”而不是只把题刷完。每一笔分，都会把你往更稳的段位推一点。</p>
          </article>
          <article class="rule-card">
            <strong>2. 段位怎么升</strong>
            <p>段位按累计积分固定晋级，从青铜一路冲到王者。越往后门槛越高，越说明你的正确率和节奏正在真正稳定下来。</p>
          </article>
          <article class="rule-card">
            <strong>3. 怎么和升本挂钩</strong>
            <p>升本最终看卷面分，而卷面分来自大量知识点的稳定正确输出。段位越高，通常越接近“考场上会做、能写、敢拿分”的状态。</p>
          </article>
        </div>
        <div class="milestone-strip" aria-label="段位晋级规则">
          <article
            v-for="item in levelMilestones"
            :key="item.code"
            :class="[
              'milestone-card',
              { 'milestone-card--reached': item.reached },
              { 'milestone-card--active': item.active },
            ]"
            :style="buildLevelCardStyle(item)"
          >
            <div class="milestone-card__image-wrap">
              <img :src="item.image" :alt="`${item.name}段位图`" class="milestone-card__image">
            </div>
            <span>{{ item.rangeLabel }}</span>
            <strong>{{ item.name }}</strong>
            <p>{{ item.cue }}</p>
          </article>
        </div>
      </article>

      <article class="drive-panel">
        <div class="drive-panel__hero">
          <span class="points-eyebrow">升本动力</span>
          <h4>段位不是装饰，它在提前暴露你的升本趋势</h4>
          <p>{{ progressActionCopy }}</p>
        </div>
        <div class="drive-callout">
          <strong>{{ momentumCopy }}</strong>
          <p>
            {{ summary.rank ? `当前同科目排名 #${summary.rank}。` : '当前还没有进入同科目榜单前列。' }}
            {{ nextLevelName ? `只差 ${pointsToNextLevel} 分就能升到 ${nextLevelName}。` : '你已经达到当前科目的最高段位。' }}
          </p>
        </div>
        <div class="success-link-list">
          <article v-for="item in successConnectionItems" :key="item.title" class="success-link-card">
            <strong>{{ item.title }}</strong>
            <p>{{ item.description }}</p>
          </article>
        </div>
      </article>
    </section>

    <section class="award-panel">
      <div class="award-panel__head">
        <div>
          <span class="points-eyebrow">段位总进度</span>
          <h4>{{ currentLevelName }}</h4>
        </div>
        <el-progress :percentage="scorePercent" :status="summary.isTopLevel ? 'success' : undefined" />
      </div>
      <p>当前总进度 {{ cappedTotal }}/{{ scoreCap }}。{{ levelProgressCopy }}；同科目排名 {{ summary.rank ? `#${summary.rank}` : '未上榜' }}。</p>
      <div class="award-panel__actions">
        <el-button plain @click="navigateToModule(STUDENT_PRACTICE_MODULE.CHAPTER)">继续章节闯关</el-button>
        <el-button plain @click="navigateToModule(STUDENT_PRACTICE_MODULE.FREE)">去自由练习</el-button>
        <el-button type="primary" plain @click="navigateToModule(STUDENT_PRACTICE_MODULE.MOCK)">去模拟考试</el-button>
      </div>
    </section>

    <section class="leaderboard-panel">
      <div class="leaderboard-panel__head">
        <div>
          <span class="points-eyebrow">排行榜</span>
          <h4>{{ selectedSubjectName }} Top 榜</h4>
        </div>
      </div>
      <div v-if="leaderboardRows.length" class="leaderboard-list">
        <article
          v-for="item in leaderboardRows"
          :key="`${item.studentUserId}-${item.rank}`"
          class="leaderboard-row"
        >
          <span class="leaderboard-rank">#{{ Number(item.rank || 0) }}</span>
          <div class="leaderboard-main">
            <strong>{{ item.studentName || '同学' }}</strong>
            <small>{{ Number(item.totalPoints || 0) }} 分</small>
          </div>
        </article>
      </div>
      <el-empty v-else description="当前还没有排行榜数据，先去刷一轮把榜单点亮。" />
    </section>
  </section>
</template>

<style scoped>
.points-page {
  display: grid;
  gap: 20px;
}

.boost-entry-banner,
.points-hero,
.rules-panel,
.drive-panel,
.award-panel,
.leaderboard-panel,
.points-metric {
  border-radius: 28px;
  border: 1px solid rgba(191, 219, 254, 0.48);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.06);
}

.boost-entry-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 24px;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.98), rgba(255, 247, 237, 0.98));
}

.boost-entry-banner__copy {
  display: grid;
  gap: 8px;
}

.boost-entry-banner__copy h4,
.boost-entry-banner__copy p {
  margin: 0;
}

.boost-entry-banner__copy p {
  color: var(--qb-text-copy);
  line-height: 1.7;
}

.boost-entry-banner__actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.points-hero {
  display: grid;
  gap: 18px;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.88fr) minmax(320px, 0.92fr);
  padding: 24px;
  background:
    radial-gradient(circle at top right, rgba(219, 234, 254, 0.75), transparent 34%),
    radial-gradient(circle at bottom left, rgba(255, 237, 213, 0.65), transparent 42%),
    rgba(255, 255, 255, 0.92);
}

.points-hero__copy {
  display: grid;
  gap: 10px;
  align-content: start;
}

.points-hero__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.points-hero__subject-label {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(239, 246, 255, 0.96);
  color: var(--qb-primary-student);
  font-size: 12px;
  font-weight: 700;
}

.points-eyebrow {
  color: var(--qb-text-meta);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.points-hero__copy h3,
.points-hero__copy p,
.rank-showcase h4,
.rank-showcase p,
.share-lab h4,
.share-lab__copy,
.award-panel h4 {
  margin: 0;
}

.points-hero__copy h3 {
  font-size: 28px;
  line-height: 1.2;
  color: var(--qb-text-heading);
}

.points-hero__copy p {
  color: var(--qb-text-copy);
}

.points-hero__summary {
  max-width: 38rem;
  font-size: 15px;
  line-height: 1.75;
}

.points-hero__stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 4px;
  border-radius: 20px;
  border: 1px solid rgba(191, 219, 254, 0.56);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 251, 255, 0.96));
  overflow: hidden;
}

.points-hero__stat-card {
  display: grid;
  gap: 4px;
  min-height: 96px;
  align-content: center;
  padding: 14px 16px;
  background: transparent;
}

.points-hero__stat-card + .points-hero__stat-card {
  border-left: 1px solid rgba(191, 219, 254, 0.56);
}

.points-hero__stat-card span,
.points-hero__stat-card small {
  color: var(--qb-text-meta);
}

.points-hero__stat-card span {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.points-hero__stat-card strong {
  color: var(--qb-text-heading);
  font-size: 24px;
  line-height: 1.1;
}

.points-hero__stat-card small {
  font-size: 11px;
  line-height: 1.45;
}

.points-hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.points-tag {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(191, 219, 254, 0.56);
  color: var(--qb-text-info-ink);
  font-size: 11px;
  font-weight: 700;
}

.rank-showcase {
  display: grid;
  gap: 12px;
  align-content: start;
  padding: 18px 18px 16px;
  border-radius: 26px;
  background: linear-gradient(160deg, var(--points-rank-from), var(--points-rank-to));
  box-shadow: 0 18px 40px var(--points-rank-glow);
  color: white;
}

.rank-showcase__main {
  display: grid;
  gap: 12px;
  grid-template-columns: 92px minmax(0, 1fr);
  align-items: center;
}

.rank-showcase__image-wrap {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 88px;
  padding: 2px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.12);
}

.rank-showcase__image {
  width: 100%;
  max-width: 76px;
  height: auto;
  display: block;
}

.rank-showcase__content {
  display: grid;
  gap: 6px;
}

.rank-showcase__content .points-eyebrow,
.rank-showcase__content p {
  color: rgba(255, 255, 255, 0.86);
}

.rank-showcase__content h4 {
  font-size: 22px;
  line-height: 1.2;
}

.rank-showcase__content p {
  font-size: 13px;
  line-height: 1.65;
}

.rank-showcase__stats {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.rank-showcase__stats article {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.16);
}

.rank-showcase__stats span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.72);
}

.rank-showcase__stats strong {
  font-size: 20px;
}

.share-lab {
  display: grid;
  gap: 14px;
  align-content: start;
  padding: 18px;
  border-radius: 26px;
  background: rgba(255, 255, 255, 0.94);
}

.share-lab__head {
  display: grid;
  gap: 14px;
}

.share-lab__subject-select {
  width: min(100%, 220px);
}

.share-lab__head h4 {
  font-size: 24px;
  color: var(--qb-text-heading);
}

.share-lab__copy {
  color: var(--qb-text-copy);
  line-height: 1.7;
}

.share-lab__qr-card {
  display: grid;
  gap: 14px;
  grid-template-columns: 132px minmax(0, 1fr);
  padding: 16px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.92), rgba(255, 247, 237, 0.88));
}

.share-lab__qr-frame {
  display: grid;
  place-items: center;
  min-height: 132px;
  padding: 10px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.92);
}

.share-lab__qr-image {
  width: 100%;
  height: auto;
  display: block;
}

.share-lab__qr-placeholder {
  color: var(--qb-text-meta);
  font-size: 13px;
}

.share-lab__qr-copy {
  display: grid;
  gap: 8px;
  align-content: start;
}

.share-lab__qr-copy strong {
  color: var(--qb-text-heading);
}

.share-lab__qr-copy p {
  margin: 0;
  color: var(--qb-text-copy);
  line-height: 1.7;
}

.share-lab__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.points-story-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: minmax(0, 1.42fr) minmax(0, 1fr);
}

.leaderboard-main small {
  color: var(--qb-text-meta);
}

.rules-panel,
.drive-panel,
.award-panel,
.leaderboard-panel {
  display: grid;
  gap: 16px;
  padding: 22px 24px;
}

.rules-panel__head,
.award-panel__head,
.leaderboard-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.rules-panel__head {
  align-items: flex-start;
}

.rules-panel__head h4,
.rules-panel__head p,
.drive-panel h4,
.drive-panel p {
  margin: 0;
}

.rules-panel__head p,
.drive-panel__hero p,
.rule-card p,
.milestone-card p,
.drive-callout p,
.success-link-card p {
  color: var(--qb-text-copy);
  line-height: 1.7;
}

.rules-grid,
.success-link-list {
  display: grid;
  gap: 12px;
}

.rules-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.rule-card,
.success-link-card {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(248, 251, 255, 0.96);
}

.rule-card strong,
.success-link-card strong,
.drive-callout strong,
.milestone-card strong {
  color: var(--qb-text-heading);
}

.milestone-strip {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.milestone-card {
  display: grid;
  gap: 8px;
  min-height: 236px;
  padding: 16px 14px;
  border: 1px solid rgba(191, 219, 254, 0.5);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.88);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.milestone-card__image-wrap {
  display: flex;
  justify-content: center;
  padding: 6px 0 2px;
  border-radius: 18px;
  background: linear-gradient(160deg, var(--milestone-from), var(--milestone-to));
  box-shadow: 0 12px 26px var(--milestone-glow);
}

.milestone-card__image {
  width: 100%;
  max-width: 102px;
  height: auto;
  display: block;
}

.milestone-card span {
  color: var(--milestone-chip-text);
  font-size: 12px;
  font-weight: 700;
}

.milestone-card p {
  margin: 0;
  font-size: 12px;
}

.milestone-card--reached {
  border-color: rgba(96, 165, 250, 0.56);
  background: linear-gradient(180deg, rgba(239, 246, 255, 0.98), rgba(255, 255, 255, 0.92));
}

.milestone-card--active {
  transform: translateY(-2px);
  box-shadow: 0 18px 34px rgba(59, 130, 246, 0.16);
}

.drive-panel {
  align-content: start;
}

.drive-panel__hero {
  display: grid;
  gap: 8px;
}

.drive-callout {
  display: grid;
  gap: 8px;
  padding: 18px 20px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.92), rgba(239, 246, 255, 0.95));
}

.award-panel__actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.leaderboard-list {
  display: grid;
  gap: 12px;
}

.leaderboard-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(248, 251, 255, 0.92);
}

.leaderboard-rank {
  min-width: 54px;
  font-size: 18px;
  font-weight: 700;
  color: var(--qb-primary-student);
}

.leaderboard-main {
  display: grid;
  gap: 4px;
}

@media (max-width: 1200px) {
  .points-hero {
    grid-template-columns: 1fr;
  }

  .points-hero__copy h3 {
    font-size: 24px;
  }

  .points-hero__summary {
    font-size: 14px;
  }

  .points-hero__stats {
    grid-template-columns: 1fr;
  }

  .points-hero__stat-card {
    min-height: auto;
  }

  .points-hero__stat-card + .points-hero__stat-card {
    border-left: 0;
    border-top: 1px solid rgba(191, 219, 254, 0.56);
  }

  .rank-showcase__main {
    grid-template-columns: 82px minmax(0, 1fr);
  }

  .rank-showcase__image {
    max-width: 68px;
  }

  .milestone-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .boost-entry-banner,
  .rules-panel__head,
  .award-panel__head,
  .leaderboard-panel__head,
  .share-lab__qr-card {
    grid-template-columns: 1fr;
    display: grid;
  }

  .points-story-grid,
  .rules-grid,
  .milestone-strip {
    grid-template-columns: 1fr;
  }

  .points-hero__meta {
    gap: 8px;
  }

  .points-hero__copy h3 {
    font-size: 22px;
  }

  .points-hero__summary {
    font-size: 13px;
    line-height: 1.7;
  }

  .rank-showcase__main,
  .rank-showcase__stats {
    grid-template-columns: 1fr;
  }

  .rank-showcase__image-wrap {
    min-height: 76px;
  }

  .boost-entry-banner {
    align-items: stretch;
  }

  .share-lab__actions,
  .boost-entry-banner__actions,
  .award-panel__actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

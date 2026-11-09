/**
 * しゃべって予定帳 × Google（カレンダー・Gmail）連携
 *
 * 使い方（くわしくはアプリの ⚙︎ →「Googleカレンダー・Gmail」）
 *  1. script.google.com で新しいプロジェクトを作り、このコードを全部貼り付けて保存
 *  2. デプロイ → 新しいデプロイ → 種類「ウェブアプリ」
 *     次のユーザーとして実行：自分 / アクセスできるユーザー：全員
 *  3. 出てきた「ウェブアプリのURL」をアプリに貼る
 *
 * このコードはあなたのGoogleアカウントの中だけで動きます。
 * 下の合言葉を知っている人（＝あなたのアプリ）しか使えません。
 */
const TOKEN = '__TOKEN__';

function doGet() {
  return out({ ok: true, app: 'yotei', msg: '予定帳のGoogle連携は動いています' });
}

function doPost(e) {
  let req;
  try { req = JSON.parse(e.postData.contents); } catch (err) { return out({ ok: false, error: 'bad request' }); }
  if (!req || req.token !== TOKEN) return out({ ok: false, error: '合言葉がちがいます' });
  try {
    switch (req.action) {
      case 'ping':
        return out({ ok: true, calendar: cal().getName() });
      case 'upsertEvents':
        return out({ ok: true, results: (req.events || []).map(upsert) });
      case 'deleteEvent': {
        const ev = findEv(req.gcalId);
        if (ev) ev.deleteEvent();
        return out({ ok: true });
      }
      case 'listEvents':
        return out({ ok: true, events: listEvents(req.from, req.to) });
      case 'searchMail':
        return out({ ok: true, mails: searchMail(req.query, req.max) });
      default:
        return out({ ok: false, error: 'unknown action' });
    }
  } catch (err) {
    return out({ ok: false, error: String((err && err.message) || err) });
  }
}

function out(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
function cal() { return CalendarApp.getDefaultCalendar(); }
function tz() { return cal().getTimeZone() || Session.getScriptTimeZone(); }
function findEv(id) {
  if (!id) return null;
  try { return cal().getEventById(id); } catch (e) { return null; }
}
function dayOf(ymd) { return Utilities.parseDate(ymd + ' 12:00', tz(), 'yyyy-MM-dd HH:mm'); }
function ymdOf(d) { return Utilities.formatDate(d, tz(), 'yyyy-MM-dd'); }

// 予定を入れる（gcalId があれば書きかえる）
function upsert(x) {
  try {
    const allDay = !x.start;
    let ev = findEv(x.gcalId);
    if (ev && ev.isRecurringEvent()) ev = null; // くり返し予定はさわらない
    if (ev) {
      ev.setTitle(x.title);
      ev.setDescription(x.description || '');
      ev.setLocation(x.location || '');
      if (allDay) ev.setAllDayDate(dayOf(x.date));
      else ev.setTime(new Date(x.start), new Date(x.end));
    } else {
      const opt = { description: x.description || '', location: x.location || '' };
      ev = allDay
        ? cal().createAllDayEvent(x.title, dayOf(x.date), opt)
        : cal().createEvent(x.title, new Date(x.start), new Date(x.end), opt);
    }
    if (!allDay && x.remind != null) {
      ev.removeAllReminders();
      ev.addPopupReminder(Number(x.remind));
    }
    return { id: x.id, gcalId: ev.getId() };
  } catch (err) {
    return { id: x.id, error: String((err && err.message) || err) };
  }
}

// 期間内の予定を読む
function listEvents(from, to) {
  const start = Utilities.parseDate(from + ' 00:00', tz(), 'yyyy-MM-dd HH:mm');
  const end = Utilities.parseDate(to + ' 23:59', tz(), 'yyyy-MM-dd HH:mm');
  return cal().getEvents(start, end).map(function (ev) {
    const allDay = ev.isAllDayEvent();
    const s = allDay ? ev.getAllDayStartDate() : ev.getStartTime();
    return {
      gcalId: ev.getId(),
      title: ev.getTitle(),
      allDay: allDay,
      date: ymdOf(s),
      time: allDay ? '' : Utilities.formatDate(s, tz(), 'HH:mm'),
      dur: allDay ? 0 : Math.round((ev.getEndTime() - ev.getStartTime()) / 60000),
      recurring: ev.isRecurringEvent(),
      location: ev.getLocation() || '',
      description: (ev.getDescription() || '').slice(0, 300)
    };
  });
}

// メールを読む（予定さがし用）
function searchMail(query, max) {
  const threads = GmailApp.search(query || 'newer_than:3d', 0, Math.min(Number(max) || 10, 20));
  return threads.map(function (th) {
    const msgs = th.getMessages();
    const m = msgs[msgs.length - 1];
    return {
      subject: m.getSubject(),
      from: m.getFrom(),
      date: Utilities.formatDate(m.getDate(), tz(), 'yyyy-MM-dd HH:mm'),
      body: (m.getPlainBody() || '').replace(/\n{3,}/g, '\n\n').slice(0, 2500)
    };
  });
}

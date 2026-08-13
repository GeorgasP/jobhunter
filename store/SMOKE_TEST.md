# Smoke test — run this before submitting

Everything below has been verified logically but **never inside a real Chrome
extension**. This is the gap between "the code works" and "the product works".
Budget 20 minutes. Anything that fails, send me the exact error.

## Load it

1. `chrome://extensions` → **Developer mode** on → **Load unpacked**
2. Select `C:\Users\Panos\Desktop\JobHunt\extension`
3. The extension card appears with the target icon and **no red "Errors" button**

> A red *Errors* button means the service worker failed to start — usually an
> import path. Click it and copy the message.

---

## 1 · Install & onboarding

- [ ] A tab opened automatically on the setup screen
- [ ] Dropping a **PDF** CV shows "✅ filename · N characters read"
- [ ] Name / email / phone / LinkedIn appear under "Read from your CV"
- [ ] Title suggestions appear on step 2 and clicking one adds it as a tag
- [ ] Step 3 shows the industry buttons
- [ ] "Start searching" runs a scan and reports "N jobs match you"

Also try a **DOCX** and a **TXT** CV — three different formats, three parsers.

## 2 · Background engine

- [ ] The toolbar icon shows a badge with the number of matches
- [ ] Clicking the icon shows the popup with matches / applications / jobs
- [ ] "Scan now" in the popup finishes and the numbers change
- [ ] `chrome://extensions` → **service worker** → Console shows no red errors
- [ ] All **21 sources** succeed — no "Failed to fetch"

> The last one matters. Himalayas and WorkingNomads failed in my page-based
> test because of CORS. From the service worker with host permissions they
> should work. If they still fail here, the host permission is wrong.

## 3 · Dashboard

- [ ] Matches list renders with score rings and reason chips
- [ ] The filter chips (Remote / Posted today / Salary listed) change the list
- [ ] Settings loads your values; changing a filter and saving re-scores
- [ ] Uploading a new CV in Settings replaces the old one
- [ ] Light/dark toggle works and survives a reload

## 4 · Apply + autofill — the important one

- [ ] Press **Apply** on a match: the posting opens in a new tab
- [ ] A **"🎯 Fill with JobHunter"** button appears bottom-right on that page
- [ ] Pressing it fills name, email, phone, location, LinkedIn, cover letter
- [ ] **The CV appears attached in the file field**
- [ ] The toast reports what was filled and what was left to you
- [ ] Nothing is submitted, and fields you typed yourself are untouched

Repeat on **one posting from each**: Greenhouse, Lever, Ashby, Workable. These
have different form markup and this is where breakage is most likely.

## 5 · Pipeline

- [ ] Applied jobs show under **Prepared**
- [ ] Dragging a card to Sent / Interview moves it and the count updates
- [ ] Clicking a card opens the drawer with the cover letter and history
- [ ] "Copy letter" copies it

## 6 · Automation

- [ ] Turn on "Search automatically twice a day" if it is off
- [ ] `chrome://extensions` → service worker → Console:
      `chrome.alarms.getAll(console.log)` shows the `jobhunter-daily` alarm
- [ ] Notifications are allowed for Chrome in Windows settings

To test the alarm without waiting 12 hours, run this in the service worker
console — it fires the scan in one minute:

```js
chrome.alarms.create("jobhunter-daily", { delayInMinutes: 1 });
```

- [ ] After a minute: a notification appears and the badge updates

## 7 · Endurance

- [ ] Run three scans in a row. The second and third should report **0 new**
- [ ] Scans stay under ~10 seconds
- [ ] `chrome.storage.local.getBytesInUse(null, console.log)` in the service
      worker console — expect a few MB, not hundreds

---

## When everything above is ticked

The gap is closed. Then it is only the four things in `SUBMISSION.md`:
developer account ($5), hosted privacy policy URL, four screenshots, and the
listing form.

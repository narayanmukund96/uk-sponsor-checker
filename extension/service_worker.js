importScripts("matcher.js");

const MENU_ID = "uk-sponsor-checker-check-selection";
const DATASET_PATH = "data/sponsors.json";
const OFFICIAL_SOURCE_URL = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers";

let matcherPromise;

function registerContextMenu() {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: MENU_ID,
      title: "Check UK sponsorship",
      contexts: ["selection"]
    });
  });
}

chrome.runtime.onInstalled.addListener(registerContextMenu);
chrome.runtime.onStartup.addListener(registerContextMenu);

async function getMatcher() {
  if (!matcherPromise) {
    matcherPromise = fetch(chrome.runtime.getURL(DATASET_PATH))
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Dataset load failed: ${response.status}`);
        }
        return response.json();
      })
      .then((dataset) => new UkSponsorCheckerMatcher.SponsorMatcher(dataset));
  }
  return matcherPromise;
}

function errorResult(input) {
  return {
    state: "error",
    input: input || "",
    normalizedInput: "",
    candidates: [],
    datasetVersion: null,
    metadata: {},
    error: "Unable to verify using the current dataset.",
    officialSourceUrl: OFFICIAL_SOURCE_URL
  };
}

async function ensureContentScript(tabId) {
  await chrome.scripting.insertCSS({
    target: { tabId },
    files: ["content.css"]
  });
  await chrome.scripting.executeScript({
    target: { tabId },
    files: ["content.js"]
  });
}

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId !== MENU_ID || !tab || !tab.id) return;

  const selectedText = info.selectionText || "";
  Promise.all([getMatcher(), ensureContentScript(tab.id)])
    .then(([matcher]) => matcher.match(selectedText))
    .catch(() => errorResult(selectedText))
    .then((result) => {
      result.officialSourceUrl = OFFICIAL_SOURCE_URL;
      return chrome.tabs.sendMessage(tab.id, {
        type: "UK_SPONSOR_CHECK_RESULT",
        result
      });
    })
    .catch(() => {
      chrome.action.setBadgeText({ tabId: tab.id, text: "!" });
      chrome.action.setTitle({
        tabId: tab.id,
        title: "UK Sponsor Checker: unable to display result on this page"
      });
    });
});

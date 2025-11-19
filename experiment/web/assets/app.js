// Error handler
const crashWithError = (e) => {
  console.error(e);
  document.getElementById("jatos-error-message").style.display = "";
  document.getElementById("jatos-error-details").innerText = e.toString();
  window.onbeforeunload = null; // Disable the warning on unload
}
window.onerror = (message, source, lineno, colno, error) => crashWithError(error || new Error(message));
window.addEventListener("error", (ErrorEvent) => crashWithError(ErrorEvent.error || new Error(ErrorEvent.message)));
window.addEventListener("unhandledrejection", (event) => crashWithError(event.reason || new Error("Unhandled promise rejection")));


/*
*** CONTENT DEFINITIONS FOR THE EXPERIMENT ***
*/
const stimuliAB = {
  A: [
    { stimulusId: "phrases2b20" },

    { stimulusId: "Haircut16-44p1-2", anchorPosition: "first" },
    { stimulusId: "Haircut16-44p1", anchorPosition: "last" }
  ],
  B: [
    { stimulusId: "phrases2b20" },

    { stimulusId: "Haircut16-44p1-2", anchorPosition: "last" },
    { stimulusId: "Haircut16-44p1", anchorPosition: "first" }
  ],
};

const allHeadsetTestStimuli = [
  { stimulusId: "headset-test-1", durationMs: 2000, options: [{name: "A", correct: true}, {name: "B", correct: false}, {name: "C", correct: false}] },
  { stimulusId: "headset-test-2", durationMs: 2000, options: [{name: "A", correct: false}, {name: "B", correct: true}, {name: "C", correct: false}] },
  { stimulusId: "headset-test-3", durationMs: 2000, options: [{name: "A", correct: false}, {name: "B", correct: false}, {name: "C", correct: true}] },
  { stimulusId: "headset-test-4", durationMs: 2000, options: [{name: "A", correct: true}, {name: "B", correct: false}, {name: "C", correct: false}] },
];
const nHeadsetTrials = 4;
const nRequiredHeadsetToPass = 3;

const staticBase = `/static/`;
const soundBaseUrl = `${staticBase}sounds/`;

const addWavUrlsToStimuli = (l) => {
  l.forEach(s => {
    s.wavUrl = `${soundBaseUrl}${s.stimulusId}.wav`
  });
}
Object.values(stimuliAB).forEach(g => addWavUrlsToStimuli(g));
addWavUrlsToStimuli(allHeadsetTestStimuli);

const triggerCategories = [
  { name: "Chewing", soundExample: `${soundBaseUrl}example-chewing.wav` },
  { name: "Plastic Crumbling", soundExample: `${soundBaseUrl}example-plastic-crumpling.wav` },
  { name: "Pen Clicking" },
];

// const soundPlayingMp4 = `${staticBase}sound-playing.mp4`; // Experienced some issues preloading, so we use the gif
const soundPlayingGif = `${staticBase}sound-playing.gif`;
const privacyPolicyLink = `privacy.html`;

const welcomeConsentHtml = `
  <h1>Misophonia Study</h1>
  <p>Misophonia is a condition where specific everyday sounds, such as chewing and pen clicking, provoke strong discomfort.</p>
  <p>We are creating a dataset of audio clips that can be used to develop noise-cancelling headphones that selectively filter out misophonia trigger sounds.</p>
  <p>By participating in this study and rating short audio clips, you will help validate this dataset so it can be openly released for anyone to build on.</p>

  <h2>Instructions</h2>
  <p>You start by answering a brief questionnaire and selecting which types of sounds trigger you. Then, we confirm that you are wearing headphones, or are listening through speakers in a quiet environment.</p>
  <p>You will then listen to and rate some sounds mixtures that may contain trigger sounds. You can skip any sound that is too uncomfortable.</p>

  <h2>Consent</h2>
  <p>
    Your participation is voluntary, and you may skip sounds or withdraw at any time, without any consequences.
  </p>
  <p>
    Please read our <a href="${privacyPolicyLink}" target="_blank">Privacy Policy</a> describing how your data will be handled. Note that the data collected will be anonymized and made publicly available for anyone to use.
  </p>

`;
const consentCheckText = `I am 18 years or older, I have read and understood the information provided, and I consent to participate voluntarily in this study.`;

const stimuliPresentationInstructionsHtml = `
  <h1>Get ready to listen</h1>
  <p>You will now hear a series of sound clips. Please listen to each carefully. Some sounds might be triggering, but you always have the option to skip if they are too uncomfortable.</p>
  <p>After each sound, you will be asked to rate the level of discomfort or anxiety you experienced while listening to it. You will also be asked to select which sound or sounds you think you heard.</p>
`;

const headsetRetryHtml = `
  <p style="color:red;">You did not pass the check. Please read the instructions carefully and try again.</p>
`;

const headsetInstructionsHtml = `
  <p><b>Please wear a headset or listen through speakers in a quiet environment.</b></p>
  <p>You will now listen to some sound clips to test that you can hear them clearly. Please adjust your volume so it is comfortable. </p>
  <p>Afterwards, we will test that you could identify what sounds you heard.</p>
`;

const copyrightCredits = `
  Sound playing animation by <a href="https://iconscout.com/free-lottie-animation/free-headphone-animated-icon_13336964" target="_blank">
  Madness Stock on IconScout</a>.
`;

const contactInfo = `
  Contact <a href="mailto:lukt@itu.dk">lukt@itu.dk</a> for any questions or concerns regarding this study. Also refer to our <a href="${privacyPolicyLink}" target="_blank">Privacy Policy</a>.
`;

const exampleSoundPlayHtml = `<div>&#9658; Example</div>`;
const soundPlayingImgHtml = `<img src="${soundPlayingGif}" alt="Sound playing animation" style="max-width: 150px; max-height: 100%;" />`;
const soundPlayingHtml = `
  <p>Please listen to the sound playing</p>
  ${soundPlayingImgHtml}
`;

// From https://gist.github.com/keeguon/2310008
const countries = [
  {name: 'Afghanistan', code: 'AF'},
  {name: 'Åland Islands', code: 'AX'},
  {name: 'Albania', code: 'AL'},
  {name: 'Algeria', code: 'DZ'},
  {name: 'American Samoa', code: 'AS'},
  {name: 'AndorrA', code: 'AD'},
  {name: 'Angola', code: 'AO'},
  {name: 'Anguilla', code: 'AI'},
  {name: 'Antarctica', code: 'AQ'},
  {name: 'Antigua and Barbuda', code: 'AG'},
  {name: 'Argentina', code: 'AR'},
  {name: 'Armenia', code: 'AM'},
  {name: 'Aruba', code: 'AW'},
  {name: 'Australia', code: 'AU'},
  {name: 'Austria', code: 'AT'},
  {name: 'Azerbaijan', code: 'AZ'},
  {name: 'Bahamas', code: 'BS'},
  {name: 'Bahrain', code: 'BH'},
  {name: 'Bangladesh', code: 'BD'},
  {name: 'Barbados', code: 'BB'},
  {name: 'Belarus', code: 'BY'},
  {name: 'Belgium', code: 'BE'},
  {name: 'Belize', code: 'BZ'},
  {name: 'Benin', code: 'BJ'},
  {name: 'Bermuda', code: 'BM'},
  {name: 'Bhutan', code: 'BT'},
  {name: 'Bolivia', code: 'BO'},
  {name: 'Bosnia and Herzegovina', code: 'BA'},
  {name: 'Botswana', code: 'BW'},
  {name: 'Bouvet Island', code: 'BV'},
  {name: 'Brazil', code: 'BR'},
  {name: 'British Indian Ocean Territory', code: 'IO'},
  {name: 'Brunei Darussalam', code: 'BN'},
  {name: 'Bulgaria', code: 'BG'},
  {name: 'Burkina Faso', code: 'BF'},
  {name: 'Burundi', code: 'BI'},
  {name: 'Cambodia', code: 'KH'},
  {name: 'Cameroon', code: 'CM'},
  {name: 'Canada', code: 'CA'},
  {name: 'Cape Verde', code: 'CV'},
  {name: 'Cayman Islands', code: 'KY'},
  {name: 'Central African Republic', code: 'CF'},
  {name: 'Chad', code: 'TD'},
  {name: 'Chile', code: 'CL'},
  {name: 'China', code: 'CN'},
  {name: 'Christmas Island', code: 'CX'},
  {name: 'Cocos (Keeling) Islands', code: 'CC'},
  {name: 'Colombia', code: 'CO'},
  {name: 'Comoros', code: 'KM'},
  {name: 'Congo', code: 'CG'},
  {name: 'Congo, The Democratic Republic of the', code: 'CD'},
  {name: 'Cook Islands', code: 'CK'},
  {name: 'Costa Rica', code: 'CR'},
  {name: 'Cote D\'Ivoire', code: 'CI'},
  {name: 'Croatia', code: 'HR'},
  {name: 'Cuba', code: 'CU'},
  {name: 'Cyprus', code: 'CY'},
  {name: 'Czech Republic', code: 'CZ'},
  {name: 'Denmark', code: 'DK'},
  {name: 'Djibouti', code: 'DJ'},
  {name: 'Dominica', code: 'DM'},
  {name: 'Dominican Republic', code: 'DO'},
  {name: 'Ecuador', code: 'EC'},
  {name: 'Egypt', code: 'EG'},
  {name: 'El Salvador', code: 'SV'},
  {name: 'Equatorial Guinea', code: 'GQ'},
  {name: 'Eritrea', code: 'ER'},
  {name: 'Estonia', code: 'EE'},
  {name: 'Ethiopia', code: 'ET'},
  {name: 'Falkland Islands (Malvinas)', code: 'FK'},
  {name: 'Faroe Islands', code: 'FO'},
  {name: 'Fiji', code: 'FJ'},
  {name: 'Finland', code: 'FI'},
  {name: 'France', code: 'FR'},
  {name: 'French Guiana', code: 'GF'},
  {name: 'French Polynesia', code: 'PF'},
  {name: 'French Southern Territories', code: 'TF'},
  {name: 'Gabon', code: 'GA'},
  {name: 'Gambia', code: 'GM'},
  {name: 'Georgia', code: 'GE'},
  {name: 'Germany', code: 'DE'},
  {name: 'Ghana', code: 'GH'},
  {name: 'Gibraltar', code: 'GI'},
  {name: 'Greece', code: 'GR'},
  {name: 'Greenland', code: 'GL'},
  {name: 'Grenada', code: 'GD'},
  {name: 'Guadeloupe', code: 'GP'},
  {name: 'Guam', code: 'GU'},
  {name: 'Guatemala', code: 'GT'},
  {name: 'Guernsey', code: 'GG'},
  {name: 'Guinea', code: 'GN'},
  {name: 'Guinea-Bissau', code: 'GW'},
  {name: 'Guyana', code: 'GY'},
  {name: 'Haiti', code: 'HT'},
  {name: 'Heard Island and Mcdonald Islands', code: 'HM'},
  {name: 'Holy See (Vatican City State)', code: 'VA'},
  {name: 'Honduras', code: 'HN'},
  {name: 'Hong Kong', code: 'HK'},
  {name: 'Hungary', code: 'HU'},
  {name: 'Iceland', code: 'IS'},
  {name: 'India', code: 'IN'},
  {name: 'Indonesia', code: 'ID'},
  {name: 'Iran, Islamic Republic Of', code: 'IR'},
  {name: 'Iraq', code: 'IQ'},
  {name: 'Ireland', code: 'IE'},
  {name: 'Isle of Man', code: 'IM'},
  {name: 'Israel', code: 'IL'},
  {name: 'Italy', code: 'IT'},
  {name: 'Jamaica', code: 'JM'},
  {name: 'Japan', code: 'JP'},
  {name: 'Jersey', code: 'JE'},
  {name: 'Jordan', code: 'JO'},
  {name: 'Kazakhstan', code: 'KZ'},
  {name: 'Kenya', code: 'KE'},
  {name: 'Kiribati', code: 'KI'},
  {name: 'Korea, Democratic People\'S Republic of', code: 'KP'},
  {name: 'Korea, Republic of', code: 'KR'},
  {name: 'Kuwait', code: 'KW'},
  {name: 'Kyrgyzstan', code: 'KG'},
  {name: 'Lao People\'S Democratic Republic', code: 'LA'},
  {name: 'Latvia', code: 'LV'},
  {name: 'Lebanon', code: 'LB'},
  {name: 'Lesotho', code: 'LS'},
  {name: 'Liberia', code: 'LR'},
  {name: 'Libyan Arab Jamahiriya', code: 'LY'},
  {name: 'Liechtenstein', code: 'LI'},
  {name: 'Lithuania', code: 'LT'},
  {name: 'Luxembourg', code: 'LU'},
  {name: 'Macao', code: 'MO'},
  {name: 'Macedonia, The Former Yugoslav Republic of', code: 'MK'},
  {name: 'Madagascar', code: 'MG'},
  {name: 'Malawi', code: 'MW'},
  {name: 'Malaysia', code: 'MY'},
  {name: 'Maldives', code: 'MV'},
  {name: 'Mali', code: 'ML'},
  {name: 'Malta', code: 'MT'},
  {name: 'Marshall Islands', code: 'MH'},
  {name: 'Martinique', code: 'MQ'},
  {name: 'Mauritania', code: 'MR'},
  {name: 'Mauritius', code: 'MU'},
  {name: 'Mayotte', code: 'YT'},
  {name: 'Mexico', code: 'MX'},
  {name: 'Micronesia, Federated States of', code: 'FM'},
  {name: 'Moldova, Republic of', code: 'MD'},
  {name: 'Monaco', code: 'MC'},
  {name: 'Mongolia', code: 'MN'},
  {name: 'Montserrat', code: 'MS'},
  {name: 'Morocco', code: 'MA'},
  {name: 'Mozambique', code: 'MZ'},
  {name: 'Myanmar', code: 'MM'},
  {name: 'Namibia', code: 'NA'},
  {name: 'Nauru', code: 'NR'},
  {name: 'Nepal', code: 'NP'},
  {name: 'Netherlands', code: 'NL'},
  {name: 'Netherlands Antilles', code: 'AN'},
  {name: 'New Caledonia', code: 'NC'},
  {name: 'New Zealand', code: 'NZ'},
  {name: 'Nicaragua', code: 'NI'},
  {name: 'Niger', code: 'NE'},
  {name: 'Nigeria', code: 'NG'},
  {name: 'Niue', code: 'NU'},
  {name: 'Norfolk Island', code: 'NF'},
  {name: 'Northern Mariana Islands', code: 'MP'},
  {name: 'Norway', code: 'NO'},
  {name: 'Oman', code: 'OM'},
  {name: 'Pakistan', code: 'PK'},
  {name: 'Palau', code: 'PW'},
  {name: 'Palestinian Territory, Occupied', code: 'PS'},
  {name: 'Panama', code: 'PA'},
  {name: 'Papua New Guinea', code: 'PG'},
  {name: 'Paraguay', code: 'PY'},
  {name: 'Peru', code: 'PE'},
  {name: 'Philippines', code: 'PH'},
  {name: 'Pitcairn', code: 'PN'},
  {name: 'Poland', code: 'PL'},
  {name: 'Portugal', code: 'PT'},
  {name: 'Puerto Rico', code: 'PR'},
  {name: 'Qatar', code: 'QA'},
  {name: 'Reunion', code: 'RE'},
  {name: 'Romania', code: 'RO'},
  {name: 'Russian Federation', code: 'RU'},
  {name: 'RWANDA', code: 'RW'},
  {name: 'Saint Helena', code: 'SH'},
  {name: 'Saint Kitts and Nevis', code: 'KN'},
  {name: 'Saint Lucia', code: 'LC'},
  {name: 'Saint Pierre and Miquelon', code: 'PM'},
  {name: 'Saint Vincent and the Grenadines', code: 'VC'},
  {name: 'Samoa', code: 'WS'},
  {name: 'San Marino', code: 'SM'},
  {name: 'Sao Tome and Principe', code: 'ST'},
  {name: 'Saudi Arabia', code: 'SA'},
  {name: 'Senegal', code: 'SN'},
  {name: 'Serbia and Montenegro', code: 'CS'},
  {name: 'Seychelles', code: 'SC'},
  {name: 'Sierra Leone', code: 'SL'},
  {name: 'Singapore', code: 'SG'},
  {name: 'Slovakia', code: 'SK'},
  {name: 'Slovenia', code: 'SI'},
  {name: 'Solomon Islands', code: 'SB'},
  {name: 'Somalia', code: 'SO'},
  {name: 'South Africa', code: 'ZA'},
  {name: 'South Georgia and the South Sandwich Islands', code: 'GS'},
  {name: 'Spain', code: 'ES'},
  {name: 'Sri Lanka', code: 'LK'},
  {name: 'Sudan', code: 'SD'},
  {name: 'Suriname', code: 'SR'},
  {name: 'Svalbard and Jan Mayen', code: 'SJ'},
  {name: 'Swaziland', code: 'SZ'},
  {name: 'Sweden', code: 'SE'},
  {name: 'Switzerland', code: 'CH'},
  {name: 'Syrian Arab Republic', code: 'SY'},
  {name: 'Taiwan, Province of China', code: 'TW'},
  {name: 'Tajikistan', code: 'TJ'},
  {name: 'Tanzania, United Republic of', code: 'TZ'},
  {name: 'Thailand', code: 'TH'},
  {name: 'Timor-Leste', code: 'TL'},
  {name: 'Togo', code: 'TG'},
  {name: 'Tokelau', code: 'TK'},
  {name: 'Tonga', code: 'TO'},
  {name: 'Trinidad and Tobago', code: 'TT'},
  {name: 'Tunisia', code: 'TN'},
  {name: 'Turkey', code: 'TR'},
  {name: 'Turkmenistan', code: 'TM'},
  {name: 'Turks and Caicos Islands', code: 'TC'},
  {name: 'Tuvalu', code: 'TV'},
  {name: 'Uganda', code: 'UG'},
  {name: 'Ukraine', code: 'UA'},
  {name: 'United Arab Emirates', code: 'AE'},
  {name: 'United Kingdom', code: 'GB'},
  {name: 'United States', code: 'US'},
  {name: 'United States Minor Outlying Islands', code: 'UM'},
  {name: 'Uruguay', code: 'UY'},
  {name: 'Uzbekistan', code: 'UZ'},
  {name: 'Vanuatu', code: 'VU'},
  {name: 'Venezuela', code: 'VE'},
  {name: 'Viet Nam', code: 'VN'},
  {name: 'Virgin Islands, British', code: 'VG'},
  {name: 'Virgin Islands, U.S.', code: 'VI'},
  {name: 'Wallis and Futuna', code: 'WF'},
  {name: 'Western Sahara', code: 'EH'},
  {name: 'Yemen', code: 'YE'},
  {name: 'Zambia', code: 'ZM'},
  {name: 'Zimbabwe', code: 'ZW'}
];



/*
*** ENSURE ONLY ONE RUN PER BROWSER; AND ONLY ONE BROWSER PER RUN ***
*/
const getShareLink = () => {
  const code = window.jatos.studyCode;
  const origin = window.location.origin;
  return `${origin}/publix/${code}`;
};

const setCookie = (name, value, days) => {
  const d = new Date();
  d.setTime(d.getTime() + (days*24*60*60*1000));
  const expires = "expires="+ d.toUTCString();
  document.cookie = name + "=" + value + ";" + expires + ";path=/";
};
const getCookie = (name) => {
  const cname = name + "=";
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(';');
  for(let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(cname) == 0) {
      return c.substring(cname.length, c.length);
    }
  }
  return null;
};


let hasEnsuredOneBrowserPerStudy = false;
const ensureOneBrowserPerStudy = (sharePathname) => {
  // This is essentially a way to change how JATOS behaves
  // We want users to share the link they see in their browser with others, but the ones they share should get a new session
  // And we want to ensure that each browser instance only participates once

  if (hasEnsuredOneBrowserPerStudy) return;
  hasEnsuredOneBrowserPerStudy = true;

  const existingShareParam = (new URL(window.location.href)).searchParams.get("share");

  // Current URL with query parameter share=shareLink (URL encoded)
  const url = new URL(window.location.href);
  url.searchParams.set("share", sharePathname);
  window.history.replaceState({}, document.title, url.toString());

  const cookieName = `${sharePathname}-instance`
  const existing = getCookie(cookieName);
  if (existing) {
    if (existing !== window.location.pathname) {
      // Redirect to the existing cookie URL
      window.onbeforeunload = null;
      window.location.href = existing;
      return;
    }
  }
  else {
    if (existingShareParam) {
      // Already have a share param, so it must come from another browser instance
      window.onbeforeunload = null;
      window.location.pathname = decodeURIComponent(existingShareParam);
      return;
    }
    else {
      // No share param, so must be new
      setCookie(cookieName, window.location.pathname, 90);
    }
  }
};



if ((new URL(window.location.href)).searchParams.has("share")) {
  // if url has resetSession=true, clear the cookie for this share link
  if ((new URL(window.location.href)).searchParams.has("resetSession")) {
    const sharePathname = (new URL(window.location.href)).searchParams.get("share");
    const cookieName = `${sharePathname}-instance`;
    setCookie(cookieName, "", -1); // delete cookie
  }
  ensureOneBrowserPerStudy((new URL(window.location.href)).searchParams.get("share"));
}


/*
*** HELPER FUNCTIONS USED FOR DEFINING THE EXPERIMENT TIMELINE ***
*/
/* === Study state management === */
const getStudyState = async (key, defaultValue) => {
  const state = window.jatos.studySessionData || {};
  if (!(key in state)) {
    return defaultValue;
  }
  return state[key];
};

const setStudyState = async (key, callback) => {
  const state = window.jatos.studySessionData || {};
  state[key] = callback(state[key]);
  await window.jatos.setStudySessionData(state);
}

const appendResultJson = async (obj) => {
  // Copy object
  const objWithIDs = Object.assign({}, obj);
  const ids  = {};
  window.jatos.addJatosIds(ids);
  objWithIDs.jatosIds = ids;
  const jsonData = JSON.stringify(objWithIDs);
  await window.jatos.appendResultData(jsonData + "\n"); // Make data as JSONL
  console.log(`Appended result data:`, jsonData);
}

const onDataUpdate = async (data) => {
  // Save trial data unless marked otherwise (for analysis)
  if (!data.doNotSave) {
    try {
      await appendResultJson(data);
    } catch (e) {
      crashWithError(Error("Failed to append result data:", e));
    }
  }

  // Save progress for page reloading
  await setStudyState("completed", x => {
    const l = x || [];
    const newCompleted = {
      trialName: data.trialName,
      repitionIdentifierVariable: data.repitionIdentifierVariable || null,
      repitionIdentifier: data.repitionIdentifierVariable ? data[data.repitionIdentifierVariable] : null,
    }
    return l.concat([newCompleted]);
  });
};

const preloadStatus = {}
const backgroundPreload = (preloadSpec) => {
  const makeCallbacks = (fileType) => {
    const onComplete = () => { };
    const onSingleComplete = (file) => {
      preloadStatus[file] = true;
    };
    const onError = (file) => {
      crashWithError(Error(`Failed to preload ${fileType} file: ${file}`));
    };

    return [ onComplete, onSingleComplete, onError ];
  };
  for (const file of [...preloadSpec.audio, ...preloadSpec.video, ...preloadSpec.images]) {
    preloadStatus[file] = false;
  }
  jsPsych.pluginAPI.preloadAudio(preloadSpec.audio, ...makeCallbacks("audio"));
  jsPsych.pluginAPI.preloadVideo(preloadSpec.video, ...makeCallbacks("video"));
  jsPsych.pluginAPI.preloadImages(preloadSpec.images, ...makeCallbacks("images"));
};


/* === Page reload / already completed functionality === */
const includeIfNotCompleted = async (trial) => {
  const completed = await getStudyState("completed", []);
  if (trial.data?.repitionIdentifierVariable) {
    throw new Error("includeIfNotCompleted cannot handle trials with repitionIdentifierVariable. Use generateMissingProcedure instead.");
  }
  const isCompleted = completed.find(c => c.trialName === trial.data?.trialName);
  return Boolean(isCompleted) ? [] : [trial];
};

const filterForMissing = async (allItems, timeline) => {
  const timelineDetails = timeline.map(t => ({ trialName: t.data?.trialName, repitionIdentifierVariable: t.data?.repitionIdentifierVariable || null }));
  const completed = await getStudyState("completed", []);
  // Filter out items that have already been completed for all timeline entries
  return allItems.filter(item => {
    const alreadyCompleted = timelineDetails.every(td => {
      return completed.find(c => {
        return c.trialName === td.trialName &&
               c.repitionIdentifierVariable === td.repitionIdentifierVariable &&
               (td.repitionIdentifierVariable === null || c.repitionIdentifier === item[td.repitionIdentifierVariable]);
      });
    });
    return !Boolean(alreadyCompleted);
  });
};


/* === Condition assignment (A/B balancing) === */
const ensureConditionAB = async () => {
  const jatos = window.jatos;

  const createIfMissing = async () => {
    // Prepare Batch Session structure if missing
    if (!jatos.batchSession.defined("/counts")) {
      await jatos.batchSession.add("/counts", { A: 0, B: 0 });
    }
  };


  // Compute balanced condition from current counts
  const calculateAssignment = async () => {
    const counts = jatos.batchSession.find("/counts");
    return counts.A === counts.B ? (Math.random() < 0.5 ? "A" : "B") : counts.A < counts.B ? "A" : "B";
  };

  // Write assignment (with simple retry to handle rare race conditions)
  const commitAssignment = async (condition) => {
    const ts = Date.now();
    // Save to result data which will be analyzed in the end, use 'trialName' for compatibility with the other data
    await appendResultJson({ trialName: "assignCondition", assignmentCondition: condition, assignmentTimestamp: ts });
    await setStudyState("condition", () => condition);

    // Increment the bucket's count using replace
    const freshCounts = jatos.batchSession.find("/counts") || { A: 0, B: 0 };
    const next = (freshCounts[condition] || 0) + 1;
    await jatos.batchSession.replace(`/counts/${condition}`, next);
  };

  let condition = await getStudyState("condition", null);

  if (condition) {
    console.log(`Reusing existing condition from Study Session: ${condition}`);
    return condition;
  }

  try {
    condition = await calculateAssignment();
  } catch (e) {
    await createIfMissing();
    condition = await calculateAssignment();
  }
  await commitAssignment(condition);
  console.log(`Assigned new condition: ${condition}`);
  return condition;
};


/* === Initialize === */
const mainTimeline = []; // Define now (so it can be dynamically modified), set in the end.
const isJATOS = typeof window.jatos !== "undefined";
if (!isJATOS) {
  alert("An error occurred while initializing the experiment. Please try again later. (Code: No JATOS)");
}
window.onbeforeunload = () => {
    return "Are you sure you want to leave? Some progress might be lost.";
};
const jsPsych = initJsPsych({
  show_progress_bar: true,
  on_data_update: onDataUpdate,
});


/* === Helpers for HTML structures === */
const makeFieldset = (categories, legend, hint, name) => `
  <fieldset class="rating-fieldset" style="margin-top:2rem;" aria-labelledby="cat-legend">
    <legend class="rating-legend" id="cat-legend">
      ${legend}
    </legend>

    <p class="rating-hint">${hint}</p>

    <input type="hidden" name="${name}" id="${name}-hidden" required />
    <input type="text" id="${name}" name="${name}" required autocomplete="off" class="visually-hidden-validator" />

    <div class="rating-stack" role="group" aria-label="Sound category (choose one or more)">
      ${categories.map(item => {
        const otherDetailsId = item.isOther ? `${item.val}-other-details` : null;
        return `
          <div class="rating-option-container">
            <div class="rating-option">
              <input class="rating-input category-input" type="checkbox"
                      id="${item.val}" value="${item.val}" data-exclusivity-group="${item.exclusivityGroup}" data-other-details-id="${otherDetailsId}" />
              <label class="rating-label" for="${item.val}">
                <span class="rating-text">${item.name}</span>
              </label>
              ${ otherDetailsId ? `
                  <input type="text" id="${otherDetailsId}" class="rating-other-input" placeholder="Please specify. Separate by comma" style="display:none;" />
                ` : "" }
            </div>

            ${ item.soundExample ? `
              <div class="example-audio-container">
                <div class="example-audio-control" data-audio-id="${item.val}-audio">${exampleSoundPlayHtml}</div>
                <audio id="${item.val}-audio" src="${item.soundExample}"></audio>
              </div>
          ` : "" }

          </div>
        `;
      }).join("")}
    </div>
  </fieldset>
`;

const fieldsetOnLoad = (name) => {
  return () => {
    const hidden = document.getElementById(name);
    const boxes = Array.from(document.querySelectorAll('.category-input'));

    function syncState(changed) {
      // Enforce only one exclusivity group selected
      if (changed) {
        const changedGroup = changed.getAttribute("data-exclusivity-group");
        boxes.forEach(b => {
          if (b !== changed && b.getAttribute("data-exclusivity-group") !== changedGroup) {
            b.checked = false;
          }
        });
      }

      // Collect selected values
      const selected = boxes.filter(b => b.checked).map(b => b.value);

      document.querySelectorAll('.rating-other-input').forEach(input => {
        if (boxes.find(b => b.getAttribute("data-other-details-id") === input.id).checked) {
          input.style.display = "block";
        } else {
          input.style.display = "none";
        }
      });
      const otherDetails = Array.from(document.querySelectorAll('.rating-other-input'))
        .filter(i => i.style.display !== "none")
        .map(input => {
          const val = input.value.trim();
          return { otherId: input.id, otherDetails: val };
        });

      // Required: at least one selected
      if (selected.length === 0) {
        hidden.value = "";
        hidden.setCustomValidity("Please select at least one category.");
      } else {
        hidden.value = JSON.stringify(selected.concat(otherDetails)); // saved as a JSON array string
        hidden.setCustomValidity("");
      }
    }

    boxes.forEach(b => b.addEventListener('change', () => syncState(b)));
    Array.from(document.querySelectorAll('.rating-other-input')).forEach(i => i.addEventListener('input', () => syncState(null)));
    // Initialize validity on page load
    syncState(null);

    // Onclick example-audio-control
    const stopAudioPlayback = (audioElem, control) => {
      audioElem.pause();
      control.innerHTML = exampleSoundPlayHtml;

    };
    const startAudioPlayback = (audioElem, control) => {
      // Look at me not caring to learn actualy CSS LOL
      const maxHeight = control.parentElement.parentElement.querySelector(".rating-option .rating-label").getBoundingClientRect().height;
      console.log("Setting audio control height to:", maxHeight);
      control.parentElement.style.height = `${maxHeight}px`;

      // If currently playing, end
      if (!audioElem.paused) {
        stopAudioPlayback(audioElem, control);
        audioElem.currentTime = 0;
      }
      else {
        audioElem.currentTime = 0;
        audioElem.play();
        control.innerHTML = soundPlayingImgHtml;
        audioElem.onended = () => stopAudioPlayback(audioElem, control);
      }
    };

    document.querySelectorAll('.example-audio-control').forEach(control => {
      control.addEventListener('click', () => {
        // Set soundPlayingImgHtml
        const previousInnerHTML = control.innerHTML;
        control.innerHTML = soundPlayingImgHtml;
        const audioId = control.getAttribute('data-audio-id');
        const audioElem = document.getElementById(audioId);

        // Stop others
        document.querySelectorAll('.example-audio-control').forEach(otherControl => {
          if (otherControl !== control) {
            const otherAudioId = otherControl.getAttribute('data-audio-id');
            const otherAudioElem = document.getElementById(otherAudioId);
            stopAudioPlayback(otherAudioElem, otherControl);
          }
        });

        startAudioPlayback(audioElem, control);
      });
    });
  }
}


/*
*** EXPERIMENT TIMELINE DEFINITIONS ***
*/
/* Welcome message */
const welcomeConsentPage = {
    type: jsPsychSurveyHtmlForm,
    data: {
      trialName: "welcomeConsent"
    },
    dataAsArray: true,
    preamble: `
      <div class="custom-content-container">
        ${welcomeConsentHtml}
      </div>
    `,
    html: `
      <label style="font-weight: bold;">
        <input type="checkbox" name="consent" value="yes" required>
        ${consentCheckText}
      </label>
      <br><br>
    `
  };



/* === Demographics === */
const demographicsPage = {
  type: jsPsychSurveyHtmlForm,
  data: {
      trialName: "demographics"
  },
  dataAsArray: true,
  preamble: '<p><b>Information about you</b></p>',
  html: `
    <label for="age">Age:</label>
    <select name="age" id="age" required>
      <option value="" disabled selected>Select your age range</option>
      ${[
        "18-24",
        "25-34",
        "35-44",
        "45-54",
        "55-64",
        "65+"
      ].map(interval => `<option value="${interval}">${interval}</option>`).join('')}
    </select>
    <br><br>
    <label for="gender">Gender:</label>
    <select name="gender" id="gender" required>
      <option value="" disabled selected>Select your gender</option>
      <option value="female">Female</option>
      <option value="male">Male</option>
      <option value="other">Other</option>
      <option value="prefer-not-to-say">Prefer not to say</option>
    </select>
    <br><br>
    <label for="country">Country of residence:</label>
    <br>
    <select name="country" id="country" required>
      <option value="" disabled selected>Select your country</option>
      <option value="no-answer">Prefer not to say</option>
      ${
        countries
          .map(c => `<option value="${c.code}">${c.name}</option>`)
          .join('')
      }
    </select>
    <br><br>
  `
};


/* === DMQ Questionnaire === */
// From https://psychiatry.duke.edu/duke-center-misophonia-and-emotion-regulation/resources/resources-clinicians-researchers
const dmqIntro = `
The following questions refer to the experience of being intensely bothered by a sound or sounds, even when they are not overly loud. These can be human or non-human sounds, or the sight of someone or something making a sound that you can't hear (e.g., the sight of someone biting their nails from across the room).
`;

const dmqLikertScale = [
  "Never",
  "Rarely",
  "Sometimes",
  "Often",
  "Always/almost always"
];

const dmqInstructionCognitive = "In the past month on average, when intensely bothered by a sound or sounds, please rate how often you had each of the following thoughts.";
const dmqQuestionsCognitive = [
  "I am helpless",
  "I want to cry",
  "How do I make this sound stop?",
  "Everything is awful.",
  "I cannot handle this",
  "I need to get away from the sound.",
  "I would do anything to make it stop.",
  "I thought about screaming at, yelling at, or telling off the person making the sound.",
  "I thought about pushing, poking, shoving, etc. the person making the sound.",
  "I thought about physically hurting the person making the sound.",
];

const dmqInstructionPhysiological = "In the past month on average, when intensely bothered by a sound or sounds, please rate how often each of the following happened to you.";
const dmqQuestionsPhysiological = [
  "I became rigid or stiff.",
  "I trembled or shuddered.",
  "My heart pounded or raced.",
  "I started breathing intensely or forcefully.",
  "I reflexively jumped.",
];

const dmqInstructionAffective = "In the past month on average, when intensely bothered by a sound or sounds, please rate how often you felt each of the following:";
const dmqQuestionsAffective = [
  "I felt angry.",
  "I felt anxious.",
  "I felt disgusted.",
  "I felt panic.",
  "I felt hostile.",
  "I felt jittery.",
  "I felt frustrated.",
];

const dmqPage = {
  type: jsPsychSurveyLikert,
  data: {
      trialName: "dmq",
      subscale: jsPsych.timelineVariable("subscale"),
      repitionIdentifierVariable: "subscale",
  },
  preamble: () => `
    <p class="dmq-intro">${dmqIntro}</p>
    <p><b>${jsPsych.evaluateTimelineVariable("instructions")}</b></p>
  `,
  questions: () => jsPsych.evaluateTimelineVariable("questions").map(question => {
    return {
      prompt: question,
      name: question,
      labels: dmqLikertScale,
      required: true
    };
  }),
  randomize_question_order: false
};

const generateDMQProcedure = async () => {
  const dmqTimeline = [dmqPage];
  const missingDMQ = await filterForMissing( [
      { subscale: "affective", instructions: dmqInstructionAffective, questions: dmqQuestionsAffective },
      { subscale: "physiological", instructions: dmqInstructionPhysiological, questions: dmqQuestionsPhysiological },
      { subscale: "cognitive", instructions: dmqInstructionCognitive, questions: dmqQuestionsCognitive },
    ], dmqTimeline);
  if (missingDMQ.length === 0) {
    return [];
  }
  return [{
      timeline: dmqTimeline,
      timeline_variables: missingDMQ,
  }];

};


/* === Trigger declaration === */
const triggerDeclarePage = {
  type: jsPsychSurveyHtmlForm,
  data: {
    trialName: "triggerDeclaration",
  },
  preamble: `
    <p class="dmq-intro">${dmqIntro}</p>
  `,
  html: makeFieldset(
    triggerCategories
      .map(c => { return { name: c.name, val: c.name, exclusivityGroup: "cat", soundExample: c.soundExample }; })
      .concat([{ name: "Others", val: "Others", exclusivityGroup: "cat", isOther: true },
        { name: "None of the above", val: "None", exclusivityGroup: "None" }])
    ,
    "Select the sounds and/or sights that bother you much more intensely than they do most other people.",
    "Select one or more options.",
    "trigger-categories"
  ),
  on_load: fieldsetOnLoad("trigger-categories"),
};


/* === Headset test === */
/* = Preload = */
const preloadPage = {
  type: jsPsychCallFunction,
  data: {
    doNotSave: true,
    trialName: "preload",
    stimulusId: jsPsych.timelineVariable("stimulusId"),
    repitionIdentifierVariable: "stimulusId",
  },
  async: true,
  func: async (done) => {
    // Set loading message
    document.querySelector("#jspsych-content").innerHTML = `
      <div class="custom-content-container">
        <p>Loading sound, please wait ...</p>
        <div class="loader"></div>
        <div style="max-height:1px;overflow:hidden;">
          ${soundPlayingHtml}
        </div>
      </div>
    `;

    // Wait for all to be preloaded
    const wavUrl = jsPsych.evaluateTimelineVariable("wavUrl");
    const isDoneLoading = () => {
      return preloadStatus[wavUrl] && preloadStatus[soundPlayingGif];
    };

    while (!isDoneLoading()) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    document.querySelector("#jspsych-root").innerHTML = ``;
    done({});
  }
};

const sampleHeadsetTest = async () => {
  const shuffled = allHeadsetTestStimuli.sort(() => 0.5 - Math.random());
  return shuffled.slice(0, nHeadsetTrials);
};


const generateHeadsetTestProcedure = async (sampledHeadsetStimuli, isRetry) => {
  // Get studySessionData -> completedHeadset
  const hasCompletedHeadset = await getStudyState("completedHeadset", false);
  if (hasCompletedHeadset) {
    return [];
  }

  isRetry = isRetry || await getStudyState("completedHeadset", null) === false;

  let numCorrect = 0;

  const headsetInstructionsPage = {
    type: jsPsychHtmlButtonResponse,
    data: {
      doNotSave: true,
      trialName: "headsetInstructions",
      isHeadsetTest: true,
    },
    stimulus: `
      <div class="custom-content-container">
        ${isRetry ? headsetRetryHtml : ''}
        ${headsetInstructionsHtml}
      </div>
    `,
    choices: ["Continue"],
  };

  const headsetPresentPage = {
      type: jsPsychAudioButtonResponse,
      data: {
        doNotSave: true,
        trialName: "headsetPresentation",
        isHeadsetTest: true,
        stimulusId: jsPsych.timelineVariable("stimulusId"),
        repitionIdentifierVariable: "stimulusId",
      },
      stimulus: jsPsych.timelineVariable("wavUrl"),
      trial_duration: jsPsych.timelineVariable("durationMs"),
      choices: [],
      prompt: soundPlayingHtml,
  };

  const headsetAnswerPage = {
    type: jsPsychSurveyHtmlForm,
    data: {
      doNotSave: true,
      trialName: "headsetAnswer",
      isHeadsetTest: true,
      stimulusId: jsPsych.timelineVariable("stimulusId"),
      repitionIdentifierVariable: "stimulusId",
    },
    html: () => {
      // One button per option. WShould submit immediately on selection.
      const options = jsPsych.evaluateTimelineVariable("options");
      return makeFieldset(
        options.map(o => { return { name: o.name, val: `${o.name}-${o.correct ? "true" : "false"}`, exclusivityGroup: o.name }; }),
        "Select the sound you heard",
        "Select one option.",
        "headsetIsCorrect"
      );
    },
    on_load: fieldsetOnLoad("headsetIsCorrect"),
    on_finish: (data) => {
      const isCorrect = data.response.headsetIsCorrect.endsWith(`true"]`)
      if (isCorrect) {
        numCorrect += 1;
      }
    },
    button_label: "Continue",
  };

  const headsetTestTimeline = {
    timeline: [preloadPage, headsetPresentPage, headsetAnswerPage],
    data: {
      isHeadsetTest: true,
    },
    randomize_order: false,
    timeline_variables: sampledHeadsetStimuli,
  };

  const headsetEvaluatePage = {
    type: jsPsychCallFunction,
    data: {
      trialName: "headsetTestEvaluation",
      isHeadsetTest: true,
    },
    async: true,
    func: async (done) => {
      const passed = numCorrect >= nRequiredHeadsetToPass;
      console.log(`Headset test completed: ${numCorrect} correct out of ${sampledHeadsetStimuli.length}. Passed: ${passed}`);

      if (passed) {
        setStudyState("completedHeadset", () => true);
        return done({passed: true, numCorrect: numCorrect});
      }

      setStudyState("completedHeadset", () => false);
      const newSamples = await sampleHeadsetTest();
      const retryHeadsetTestProcedure = await generateHeadsetTestProcedure(newSamples, true);
      console.log("Retrying headset test procedure:", retryHeadsetTestProcedure);
      const currentHeadsetTests = mainTimeline.findIndex(t => t.data?.isHeadsetTest);
      const headsetTestLength = mainTimeline.filter(t => t.data?.isHeadsetTest).length;
      mainTimeline.splice(currentHeadsetTests, headsetTestLength, ...retryHeadsetTestProcedure);
      mainTimeline.unshift(...Array(headsetTestLength).fill({})); // Add headsetTestLength empty elements to the beginning of the timeline to keep the timeline index correct
      done({passed: false, numCorrect: numCorrect});
    },
  };

  return [ headsetInstructionsPage, headsetTestTimeline, headsetEvaluatePage ];
};



/* === Stimulus presentation and rating === */
/* = Stimulus presentation = */
const stimulusPresentPage = {
    type: jsPsychAudioButtonResponse,
    data: {
      trialName: "stimuliPresentation",
      stimulusId: jsPsych.timelineVariable("stimulusId"),
      repitionIdentifierVariable: "stimulusId",
    },
    stimulus: jsPsych.timelineVariable("wavUrl"),
    trial_duration: 30000,
    choices: ['Sound is too uncomfortable, stop playback'],
    prompt: soundPlayingHtml,
};

/* = Stimulus rating = */
const stimulusRatingButtons = [
  { label: "5", color: "#e20001" },
  { label: "4", color: "#e25800" },
  { label: "3", color: "#e8b30f" },
  { label: "2", color: "#e2d70b" },
  { label: "1", color: "#97e600" },
  { label: "0", color: "#2ae204" },
];
const stimulusRatePage = {
  type: jsPsychSurveyHtmlForm,
  data: {
    trialName: "stimulusRating",
    stimulusId: jsPsych.timelineVariable("stimulusId"),
    repitionIdentifierVariable: "stimulusId",
    wavUrl: jsPsych.timelineVariable("wavUrl")
  },
  html: () =>  `
    <fieldset class="rating-fieldset">
      <legend class="rating-legend">
        Rate the discomfort/anxiety you felt while hearing the sound
      </legend>

      <p class="rating-hint">Very much discomfort</p>

      <div class="rating-stack" role="radiogroup" aria-label="Discomfort rating">
        ${stimulusRatingButtons.map((btn, i) => {
          const id = `rate-${i}`;
          // Per HTML spec, “required” on ONE radio within the group makes the whole group required
          // (we set it on the first input).
          const required = i === 0 ? "required" : "";
          return `
            <div class="rating-option">
              <input class="rating-input" type="radio" name="stimuli_rating" id="${id}"
                    value="${btn.label}" ${required} />
              <label class="rating-label" for="${id}" style="--rating-color: ${btn.color}">
                <span class="rating-circle" aria-hidden="true"></span>
                <span class="rating-text">${btn.label}</span>
              </label>
            </div>`;
        }).join("")}
      </div>

      <p class="rating-hint">Very little discomfort</p>
    </fieldset>


    ${
      makeFieldset(
        triggerCategories
          .map(c => { return { name: c.name, val: c.name, exclusivityGroup: "cat" }; })
          .concat([{ name: "None of the above", val: "None", exclusivityGroup: "None" }]),
        "Which of the following categories did the sound you just heard belong to?",
        "Select one or more options.",
        "trigger-categories"
      )
    }
  `,
  button_label: "Play next sound",
  on_load: fieldsetOnLoad("trigger-categories"),
};

/* = Stimulus procedure timeline = */
const stimulusProcedureTimeline = [preloadPage, stimulusPresentPage, stimulusRatePage];
const generateStimulusPresentation = async (missingStimuli) => {
  const firstAnchorStimuli = missingStimuli.filter(s => s.anchorPosition === "first");
  const lastAnchorStimuli = missingStimuli.filter(s => s.anchorPosition === "last");
  const nonAnchorStimuli = missingStimuli.filter(s => !s.anchorPosition);

  const stimuliTimelinePart = [];

  if (firstAnchorStimuli.length > 0) {
    stimuliTimelinePart.push({
      timeline: stimulusProcedureTimeline,
      data: {
        isFirstAnchor: true,
      },
      timeline_variables: firstAnchorStimuli,
    });
  }

  if (nonAnchorStimuli.length > 0) {
    stimuliTimelinePart.push({
      timeline: stimulusProcedureTimeline,
      randomize_order: true,
      timeline_variables: nonAnchorStimuli,
    });
  }

  if (lastAnchorStimuli.length > 0) {
    stimuliTimelinePart.push({
      timeline: stimulusProcedureTimeline,
      data: {
        isLastAnchor: true,
      },
      timeline_variables: lastAnchorStimuli,
    });
  }

  if (stimuliTimelinePart.length > 0) {
    stimuliTimelinePart.unshift(
      {
        type: jsPsychHtmlButtonResponse,
        data: {
          doNotSave: true,
          trialName: "stimuliInstructions",
        },
        stimulus: `
          <div class="custom-content-container">
            ${stimuliPresentationInstructionsHtml}
          </div>
        `,
        choices: ["Play sound"],
      }
    );
  }

  return stimuliTimelinePart;
};


/* === Thank you page === */
const thanksPage = {
  type: jsPsychCallFunction,
  data: {
    trialName: "thanks",
  },
  async: true,
  func: async () => {
    window.onbeforeunload = null; // Disable the warning on unload
    const shareLink = getShareLink();
    document.querySelector("#jspsych-content").innerHTML = `
      <div class="custom-content-container">
        <h1>Thank You!</h1>
        <p>Your participation is greatly appreciated.</p>
        <p>If you would like to share this study with others, please share the following link:</p>
        <div style="display:flex;gap:.5rem;align-items:center">
          <input id="study-link" value="${shareLink}" style="flex:1;padding:.6rem;border:1px solid #ddd;border-radius:8px" readonly />
          <button id="copy-btn" style="padding:.6rem 1rem;border:0;border-radius:8px;cursor:pointer">
            Copy
          </button>
        </div>

        <p>
          If you are interested in learning more about the condition, see <a href="https://psychiatry.duke.edu/duke-center-misophonia-and-emotion-regulation/resources/resources-sufferers-loved-ones" target="_blank">the list of resources made by the Duke Center for Misophonia and Emotion Regulation</a>.
        </p>

        <p>
          ${contactInfo}
        </p>

        <p>You can now close this window.</p>

        <div class="copyright-credits">
          ${copyrightCredits}
        </div>
      </div>
    `;
    const copyBtn = document.getElementById('copy-btn');
    const input = document.getElementById('study-link');
    copyBtn?.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(input.value);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => (copyBtn.textContent = 'Copy'), 1200);
      } catch (_) {
        input.select(); document.execCommand('copy');
      }
    });
    // On select, select all text
    input?.addEventListener('focus', (event) => {
      event.target.select();
    });

    // await window.jatos.endStudyWithoutRedirect(); // Do not mark complete to allow revisiting the thank you page
  }
};


/*
*** EXPERIMENT TIMELINE INITIALIZATION AND RUNNING THE EXPERIMENT ***
*/
window.jatos.onLoad(async () => {
  console.log("JATOS is loaded");
  document.querySelector("#jatos-waiting-message").style.display = "none";
  const shareLink = getShareLink();
  ensureOneBrowserPerStudy((new URL(shareLink)).pathname);

  const condition = await ensureConditionAB();
  const allStimuliForCondition = stimuliAB[condition];
  const missingStimuli = await filterForMissing(allStimuliForCondition, stimulusProcedureTimeline);

  const sampledHeadsetStimuli = await sampleHeadsetTest();

  const filesToPreload = {
    audio: [...missingStimuli, ...sampledHeadsetStimuli].map(s => s.wavUrl),
    video: [], // Experienced issues with preloading soundPlayingMp4
    images: [soundPlayingGif],
  };
  backgroundPreload(filesToPreload);

  console.log(`Completed stimuli:`, allStimuliForCondition.length - missingStimuli.length);
  console.log(`Files to preload:`, filesToPreload);

  mainTimeline.push(
    ...await includeIfNotCompleted(welcomeConsentPage),
    ...await includeIfNotCompleted(demographicsPage),
    ...await includeIfNotCompleted(triggerDeclarePage),
    ...await generateDMQProcedure(),
    ...await generateHeadsetTestProcedure(sampledHeadsetStimuli),
    ...await generateStimulusPresentation(missingStimuli),
    thanksPage
  );

  console.log("Final timeline:", mainTimeline);

  jsPsych.run(mainTimeline);
});


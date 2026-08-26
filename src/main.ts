/// <reference types="@workadventure/iframe-api-typings" />

import { bootstrapExtra } from "@workadventure/scripting-api-extra";

console.log('Script started successfully');

let currentPopup: any = undefined;

// Waiting for the API to be ready
WA.onInit().then(() => {
    console.log('Scripting API ready');
    console.log('Player tags: ',WA.player.tags)

    WA.room.area.onEnter('clock').subscribe(() => {
        const today = new Date();
        const time = today.getHours() + ":" + today.getMinutes();
        currentPopup = WA.ui.openPopup("clockPopup", "It's " + time, []);
    })

    WA.room.area.onLeave('clock').subscribe(closePopup)

    // The line below bootstraps the Scripting API Extra library that adds a number of advanced properties/features to WorkAdventure
    bootstrapExtra().then(() => {
        console.log('Scripting API Extra ready');
    }).catch(e => console.error(e));

    // Automated map tour for QA runs: join with the player name "MapTester"
    // and the character walks the whole map on its own.
    if (WA.player.name === 'MapTester') {
        runTour().catch(e => console.error('TOUR failed', e));
    }

}).catch(e => console.error(e));

async function runTour() {
    const tiles: [number, number][] = [
        [23, 62],           // Büro
        [34, 62], [38, 56], // Osträume
        [23, 62], [23, 44], // Flur nach Norden
        [26, 34],           // 1. Hof (Parkplatz)
        [13, 34],           // vor die Garagenzeile (Westseite)
        [12, 37], [5, 37], [12, 37],  // Garage 1
        [12, 21], [5, 21], [12, 21],  // Garage 5
        [12, 9], [5, 9], [12, 9],     // HofCafé (Nordende)
        [18, 20], [17, 8],  // Weg und Garten mit Pool
        [18, 20], [26, 34], // zurück in den Hof
        [33, 31], [40, 31], [33, 31], // Holzwerkstatt (Ostseite)
        [33, 36], [40, 36], [33, 36], // Metallwerkstatt
        [26, 34],           // Hofmitte
        [23, 44], [18, 55], [19, 68], // durchs Haus nach Süden
        [18, 76], [30, 77], // Garten
        [24, 33],           // Ende: Hofmitte
    ];
    console.log('TOUR start');
    for (let i = 0; i < tiles.length; i++) {
        const [tx, ty] = tiles[i];
        const move = WA.player.moveTo(tx * 32 + 16, ty * 32 + 16, 16);
        await Promise.race([move, new Promise(res => setTimeout(res, 6000))]);
        console.log(`TOUR waypoint ${i + 1}/${tiles.length} (${tx},${ty})`);
        await new Promise(res => setTimeout(res, 400));
    }
    console.log('TOUR done');
}

function closePopup(){
    if (currentPopup !== undefined) {
        currentPopup.close();
        currentPopup = undefined;
    }
}

export {};

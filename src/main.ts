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
        [13, 62],           // Büro
        [24, 62], [28, 56], // Osträume
        [13, 62], [13, 44], // Flur nach Norden
        [16, 34],           // Parkplatz
        [8, 20], [7, 8],    // Einfahrt, Garten mit Pool
        [8, 20], [16, 34],  // zurück
        [13, 44], [8, 55], [9, 68],   // durchs Haus nach Süden
        [8, 76], [20, 77],  // Garten
        [32, 74], [32, 50], // Pflasterstreifen nach Norden
        [40, 50],           // 1. Hof
        [56, 49], [48, 50], // Garage 1 und raus
        [48, 65], [57, 65], [48, 66], // Druckwerkstatt (Doppeltor)
        [43, 60],           // Hofmitte
        [36, 71], [37, 77], [36, 71], // HofCafé
        [42, 71], [43, 77], [42, 71], // Holzwerkstatt
        [48, 71], [49, 77], [48, 71], // Metallwerkstatt
        [44, 60],           // Ende: Hofmitte
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

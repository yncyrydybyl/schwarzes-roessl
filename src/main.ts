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
    // one route per map; each route ends on the portal to the next map,
    // so a MapTester visits office -> Entwurf A -> B -> C automatically.
    const tours: [string, [number, number][]][] = [
        ['hof-a', [
            [12, 41], [4, 41], [12, 41],    // Garage 1
            [12, 21], [4, 21], [12, 21],    // Garage 5
            [12, 8], [4, 5], [12, 8],       // HofCafé (Nordblock)
            [18, 38],                        // PKW-Stellplätze
            [28, 27], [35, 27], [28, 27],   // Holzwerkstatt (Ost)
            [33, 39], [40, 39], [33, 39],   // Metallwerkstatt (Ost)
            [23, 16], [23, 13],             // Keilspitze -> Portal Entwurf B
        ]],
        ['hof-b', [
            [12, 30], [4, 30], [12, 30],    // Garage 1
            [12, 14], [4, 14], [12, 14],    // Garage 5/6
            [19, 12],                        // Diskokugel
            [28, 8], [34, 8], [28, 8],      // Holzwerkstatt
            [28, 14], [34, 14], [28, 14],   // Metallwerkstatt
            [31, 18], [33, 23], [33, 18],   // Terrasse + HofCafé
            [27, 3],                         // Portal Entwurf C
        ]],
        ['hof-c', [
            [7, 3], [7, 21],                 // Garagen-Spalte entlang
            [26, 21], [26, 15], [26, 9], [26, 3],  // Ost-Spalte
            [17, 23],                        // Mitte
        ]],
        ['office', [
            [13, 62], [13, 44],              // Büro, Flur nach Norden
            [12, 30],                        // Parkplatz
            [8, 20], [7, 8], [8, 20],        // Garten mit Pool
            [12, 36], [8, 35],               // Portale -> Entwurf A
        ]],
    ];
    const roomId = WA.room.id;
    const entry = tours.find(([key]) => roomId.includes(key)) ?? tours[3];
    const tiles = entry[1];
    console.log(`TOUR start (${entry[0]})`);
    for (let i = 0; i < tiles.length; i++) {
        const [tx, ty] = tiles[i];
        try {
            const move = WA.player.moveTo(tx * 32 + 16, ty * 32 + 16, 16);
            await Promise.race([move, new Promise(res => setTimeout(res, 6000))]);
            console.log(`TOUR waypoint ${i + 1}/${tiles.length} (${tx},${ty})`);
        } catch (e) {
            console.log(`TOUR waypoint ${i + 1}/${tiles.length} (${tx},${ty}) SKIPPED: ${e}`);
        }
        await new Promise(res => setTimeout(res, 400));
    }
    console.log(`TOUR done (${entry[0]})`);
}

function closePopup(){
    if (currentPopup !== undefined) {
        currentPopup.close();
        currentPopup = undefined;
    }
}

export {};

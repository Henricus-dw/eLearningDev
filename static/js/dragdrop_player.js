// dragdrop_player.js
// Alpine.js component for the drag-and-drop question player (v1.1.0 Phase 3d).
//
// Used by:
//   - templates/partials/players/drag_drop.html (all-on-one-page renderer)
//   - templates/proctored_assessment.html       (one-question-at-a-time wizard)
//
// Both render contexts have a small inline x-data="dragdropQuestion(...)" block
// that calls into this module. Single-occupancy zones, all-or-nothing scoring,
// decoys allowed. Form fields are q_{qid}_{item_id}=zone_id or empty.

(function () {
  if (typeof window.dragdropQuestion === 'function') return;

  window.dragdropQuestion = function (qid, items, zones) {
    return {
      qid: qid,
      items: items || [],
      zones: zones || [],
      placements: {},
      selected_item_id: null,

      // 'side'   -> items tray sits to the right of the image (default; best for
      //             portrait / square / mildly landscape backgrounds).
      // 'bottom' -> items tray sits below the image (best for wide landscape
      //             backgrounds where a side tray would shove the image into a
      //             narrow strip and shrink the zones).
      layout: 'side',

      init() {
        // Every item starts unplaced. Decoys are server-side; the client
        // does not know which items are decoys, so all items begin in the tray.
        this.items.forEach(item => { this.placements[item.id] = null; });

        // Defer the initial layout pick to the next tick so the DOM is
        // rendered. Covers two cases the @load handler can miss:
        //   1. Images cached by the browser (some browsers don't re-fire
        //      `load` for cached resources reliably).
        //   2. Multi-question wizards (proctored_assessment / quiz_take) where
        //      the Alpine component initialises before its <img> is visible.
        if (typeof this.$nextTick === 'function') {
          this.$nextTick(() => {
            if (!this.$el) return;
            const bg = this.$el.querySelector('img');
            if (bg && bg.complete && bg.naturalWidth) {
              this.onImageLoad(bg.naturalWidth, bg.naturalHeight);
            }
          });
        }
      },

      // Called from the <img @load> handler on the background. Picks side vs
      // bottom based on the actual loaded aspect ratio so the layout adapts
      // per question instead of being one-size-fits-all.
      onImageLoad(naturalWidth, naturalHeight) {
        if (!naturalWidth || !naturalHeight) return;
        const ratio = naturalWidth / naturalHeight;
        // ~1.4 is a comfortable threshold: 4:3 (1.33) stays side, 16:9 (1.78)
        // and wider drop the tray below.
        this.layout = ratio > 1.4 ? 'bottom' : 'side';
      },

      onItemTap(item_id) {
        this.selected_item_id = (this.selected_item_id === item_id) ? null : item_id;
      },

      onZoneTap(zone_id) {
        if (!this.selected_item_id) {
          // Tapping an empty selection on a zone that already holds an item
          // picks that item up so it can be re-placed elsewhere.
          const placed = this.items.find(it => this.placements[it.id] === zone_id);
          if (placed) {
            this.placements[placed.id] = null;
            this.selected_item_id = placed.id;
            this.notifyChange();
          }
          return;
        }
        this.placeItem(this.selected_item_id, zone_id);
        this.selected_item_id = null;
      },

      placeItem(item_id, zone_id) {
        // Single-occupancy: bump any other item currently in this zone
        // back to the tray before placing.
        for (const it of this.items) {
          if (this.placements[it.id] === zone_id && it.id !== item_id) {
            this.placements[it.id] = null;
          }
        }
        this.placements[item_id] = zone_id;
        this.notifyChange();
      },

      onDragStart(item_id, event) {
        if (event && event.dataTransfer) {
          event.dataTransfer.setData('text/plain', String(item_id));
          event.dataTransfer.effectAllowed = 'move';
        }
        this.selected_item_id = item_id;
      },

      onZoneDrop(zone_id, event) {
        const dt = (event && event.dataTransfer) ? event.dataTransfer.getData('text/plain') : '';
        const item_id = dt || this.selected_item_id;
        if (!item_id) return;
        this.placeItem(item_id, zone_id);
        this.selected_item_id = null;
      },

      onTrayDrop(event) {
        const dt = (event && event.dataTransfer) ? event.dataTransfer.getData('text/plain') : '';
        const item_id = dt || this.selected_item_id;
        if (!item_id) return;
        this.placements[item_id] = null;
        this.selected_item_id = null;
        this.notifyChange();
      },

      // Dispatch a bubbling 'input' event from the component root so the
      // wizard's card-level progress listener notices the placement change.
      // Hidden inputs bound via :value="placements[...]" do NOT fire DOM
      // events when their reactive value mutates, so this synthetic event is
      // required for the wizard's isAnswered() to re-evaluate after a drop.
      notifyChange() {
        if (this.$el && typeof this.$el.dispatchEvent === 'function') {
          this.$el.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }
    };
  };
})();

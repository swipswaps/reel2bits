package routers

import (
	"dev.sigpipe.me/dashie/reel2bits/context"
	"github.com/Unknwon/paginater"
	"dev.sigpipe.me/dashie/reel2bits/models"
	log "gopkg.in/clog.v1"
)

const (
	tmplTracksList = "tracks_list"
)

// NotFound [GET]
func NotFound(ctx *context.Context) {
	ctx.Title(ctx.Tr("error.page_not_found"))
	ctx.Handle(404, "home.NotFound", nil)
}

// Home [GET]
func Home(ctx *context.Context) {
	ctx.Title("Home page")
	ctx.PageIs("hub.home")

	page := ctx.QueryInt("page")
	if page <= 0 {
		page = 1
	}
	ctx.Data["PageNumber"] = page

	opts := &models.TrackOptions{
		PageSize: 10,	// TODO: put this in config
		Page: page,
		GetAll: true,
		WithPrivate: false,
		OnlyReady: true,
	}

	listOfTracks, tracksCount, err := models.GetTracks(opts)
	if err != nil {
		log.Warn("Cannot get Tracks with opts %v, %s", opts, err)
		ctx.Flash.Error(ctx.Tr("track_list.error_getting_list"))
		ctx.Handle(500, "ListTracks", err)
		return
	}

	ctx.Data["tracks"] = listOfTracks
	ctx.Data["tracks_count"] = tracksCount

	ctx.Data["Total"] = tracksCount
	ctx.Data["Page"] = paginater.New(int(tracksCount), opts.PageSize, page, 5)

	ctx.Success(tmplTracksList)
}
// Author: Mike Dezube <michael dezube at gmail dot com>
// Thank you to all who posted snippets on bl.ocks.org that helped make this possible.

// Not intended to be used directly, see createSteamgraph() for usage.
function steamgraph(data, opt_color) {
    var colors = colorbrewer[opt_color || "Spectral"][9];

    return {
        initLayout: function() {
            var boundingRect = d3.select(".chart").node()
                .getBoundingClientRect();
            this.margin = {
                top: 20,
                right: 45,
                bottom: 20,
                left: 45
            };
            this.width = boundingRect.width - this.margin.left - this.margin.right;
            this.height = boundingRect.height - this.margin.top - this.margin.bottom;

            this.svg = d3.select(".chart")
                .append("svg")
                .attr("width", this.width + this.margin.left + this.margin.right)
                .attr("height", this.height + this.margin.top + this.margin.bottom)
                .append("g")
                .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
        },
        initScales: function() {
            this.xScale = d3.time.scale()
                .range([0, this.width]);
            this.yScale = d3.scale.linear()
                .range([this.height - 10, 0]);
            this.colorScale = d3.scale.ordinal()
                .range(colors);
        },
        initAxes: function() {
            this.xAxis = d3.svg.axis()
                .scale(this.xScale)
                .orient("bottom")
                .tickFormat(steamgraph.READABLE_DATE_FORMAT);

            this.yAxis = d3.svg.axis()
                .scale(this.yScale);
        },
        drawTooltipAndBar: function() {
            this.tooltip = d3.select(".chart")
                .append("div")
                .style("position", "absolute")
                .style("z-index", "25")
                .style("visibility", "hidden")
                .style("top", "30px")
                .style("left", "155px");
            this.verticalBar = d3.select(".chart")
                .append("div")
                .style("position", "absolute")
                .style("z-index", "20")
                .style("visibility", "hidden")
                .style("width", "1px")
                .style("top", this.margin.top + 100 + "px")
                .style("bottom", this.margin.bottom + 100 + d3.select(".x.axis").node().getBoundingClientRect().height + "px")
                .style("height", "auto")
                .style("background", "#686868");
        },
        createLayersAndSetDomains: function() {
            this.layers = steamgraph.stacker(steamgraph.nester.entries(data));
            this.xScale.domain(d3.extent(data, function(d) {
                return d.date;
            }));
            this.yScale.domain([0, d3.max(data, function(d) {
                return d.y0 + d.y;
            })]);
        },
        drawLayers: function() {
            // Rebind since within the subfunctions "this" will mean something else.
            var xScale = this.xScale;
            var yScale = this.yScale;
            var colorScale = this.colorScale;

            var areaCreator = d3.svg.area()
                .interpolate("cardinal")
                .x(function(d) {
                    return xScale(d.date);
                })
                .y0(function(d) {
                    return yScale(d.y0);
                })
                .y1(function(d) {
                    return yScale(d.y0 + d.y);
                });

            this.svg.selectAll(".layer")
                .data(this.layers)
                .enter().append("path")
                .attr("class", "layer")
                .attr("d", function(d) {
                    return areaCreator(d.values);
                })
                .style("fill", function(d, i) {
                    return colorScale(i);
                })
                .attr("opacity", 1);
        },
        drawAxes: function() {
            this.svg.append("g")
                .attr("class", "x axis")
                .attr("transform", "translate(0," + this.height + ")")
                .call(this.xAxis);

            this.svg.append("g")
                .attr("class", "y axis")
                .attr("transform", "translate(" + this.width + ", 0)")
                .call(this.yAxis.orient("right"));

            this.svg.append("g")
                .attr("class", "y axis")
                .call(this.yAxis.orient("left"));
        },
        wireUpMouseListeners: function() {
            // Rebind since within the callbacks "this" will mean something else.
            var svg = this.svg;
            var xScale = this.xScale;
            var tooltip = this.tooltip;
            var verticalBar = this.verticalBar;
            var marginLeft = this.margin.left;

            svg.selectAll(".layer")
                .on("mouseover", function(d, hoveredLayerIndex) {
                    svg.selectAll(".layer")
                        .transition().duration(200)
                        .attr("opacity", function(d, j) {
                            // Fade out all but the selection layer.
                            return hoveredLayerIndex != j ? 0.1 : 1;
                        })
                })
                .on("mousemove", function(d, i) {
                    var xCoord = d3.mouse(this)[0];
                    var xValueAsTimeStamp = new Date(xScale.invert(xCoord)).getTime();
                    var valuesForLayer = d.values;

                    var smallestDiff = Number.MAX_SAFE_INTEGER;
                    var smallestDiffIdx = -1;
                    // Finds the closest x value to the hovered point.
                    // TODO convert to binary search
                    for (var xIdx = 0; xIdx < valuesForLayer.length; xIdx++) {
                        var diff = Math.abs(valuesForLayer[xIdx].date.getTime() - xValueAsTimeStamp);
                        if (diff < smallestDiff) {
                            smallestDiff = diff;
                            smallestDiffIdx = xIdx;
                        }
                    }

                    d3.select(this)
                        .attr("stroke", "black")
                        .attr("stroke-width", "0.4px"),
                        tooltip.html(
                            "<p>Person: " + d.key + "<br>" +
                            " Date Bucket: " + steamgraph.READABLE_DATE_FORMAT(valuesForLayer[smallestDiffIdx].date) + "<br>" +
                            " Texts in Bucket: " + valuesForLayer[smallestDiffIdx].value + "</p>" +
                            " Texts Total: " + steamgraph.COMMA_FORMAT(
                                d3.sum(valuesForLayer, function(x) {
                                    return x.value;
                                })) + "</p>"
                        ).style("visibility", "visible");

                    // Running in iPython we'll have jQuery() so just use that to call position().left.
                    // We add 4px to the location so the mouse is never actually over the bar and
                    // doesn't triggger the mouseout listener.
                    verticalBar
                        .style("left", xCoord + marginLeft + $('.chart').position().left + 4 + "px")
                        .style("visibility", "visible")

                })
                .on("mouseout", function(d, i) {
                    svg.selectAll(".layer")
                        .transition()
                        .duration(200)
                        .attr("opacity", "1");
                    d3.select(this)
                        .attr("stroke-width", "0px")
                })
        }
    };
}

/**
 * Draws a steamgraph with data in the passed CSV.  The CSV must have the format of:
 * date,key,value
 * YYYY/MM,John Doe,# texts exchanged in this month
 * YYYY/MM,Jane Doe,# texts exchanged in this month
 * 
 * The streamgraph is drawn with the color palette from colorbrewer.js named by opt_color, or
 * defaults to the 'Spectral' color palette.
 * 
 * This method requires there be a div with class 'chart' with a width and height set in which to
 * draw the steamgraph.
 */

function createSteamgraph(csvAsString, opt_color) {
    var data = d3.csv.parse(csvAsString, function(data) {
        return {
            key: data.key,
            date: d3.time.format("%Y/%m").parse(data.date),
            value: parseInt(data.value)
        }
    });
    steamgraph.READABLE_DATE_FORMAT = d3.time.format("%b '%y");
    steamgraph.COMMA_FORMAT = d3.format("0,000");
    steamgraph.stacker = d3.layout.stack()
        .offset("wiggle")
        .values(function(d) {
            return d.values;
        })
        .x(function(d) {
            return d.date;
        })
        .y(function(d) {
            return d.value;
        });
    steamgraph.nester = d3.nest()
        .key(function(d) {
            return d.key;
        });

    var mySteamgraph = new steamgraph(data, opt_color)

    mySteamgraph.initLayout();
    mySteamgraph.initScales();
    mySteamgraph.initAxes();

    mySteamgraph.createLayersAndSetDomains();
    mySteamgraph.drawLayers();
    mySteamgraph.drawAxes();
    mySteamgraph.drawTooltipAndBar();
    mySteamgraph.wireUpMouseListeners();
}

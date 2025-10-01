import React, { useState, useEffect } from 'react'
import { useWebSocket } from './WebSocketProvider'

interface AnalyticsChartsProps {
  data: any
  className?: string
}

interface ChartDataPoint {
  date: string
  posts: number
  responses: number
  copy_rate?: number
}

const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ data, className = '' }) => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('7d')
  const [selectedMetric, setSelectedMetric] = useState('posts')
  const [chartData, setChartData] = useState<ChartDataPoint[]>([])
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null)
  const { lastMessage } = useWebSocket()

  // Update chart data when analytics data changes
  useEffect(() => {
    if (data?.daily_activity) {
      setChartData(data.daily_activity)
    }
  }, [data])

  // Handle real-time analytics updates
  useEffect(() => {
    if (lastMessage?.type === 'analytics_update') {
      setChartData(prev => {
        const newData = [...prev]
        const today = new Date().toISOString().split('T')[0]
        const todayIndex = newData.findIndex(d => d.date === today)
        
        if (todayIndex >= 0) {
          newData[todayIndex] = { ...newData[todayIndex], ...lastMessage.data }
        } else {
          newData.push({ date: today, ...lastMessage.data })
        }
        
        return newData.slice(-30) // Keep last 30 days
      })
    }
  }, [lastMessage])

  if (!data) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-2 text-gray-600">Loading analytics...</p>
      </div>
    )
  }

  const { daily_activity = [], top_keywords = [], top_subreddits = [] } = data

  const timeRangeOptions = [
    { value: '7d', label: '
    { value: '30d', labe
    { value: '90d', la }
  ]

  const metricOp[
    { value:  },
    { value: 'responses', label: 'Responses', color: 'green' },
    { valu
  ]

  const getFilteredData = () => {
    const days = parseInt(selectedTimeRange.replace('d', ''))
    return chartData.slice(-days)
  }

  const getMaxValue = (data: ChartDataPoint[], metric: string) => {
    return Math.max(...data.map(d => (d as any)[metric] || 0))
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'nic' })
  }

  const getMetricColor = (metric: string) => {
    const colors = {
      posts: 'bg-blue-500',
      responses: 'bg-g0',
      copy_rate: 'bg'
    }
    return color-500'
  }

  const fia()
  const maxVtedMetric)

  rrn (
 me}`}>
t */}
      <div className="bg-white
}</div>
  )
        </div>)}
        ble</p>
   availaataeddit dNo subr py-4"> text-centeray-500t-gr="tex className     <p: (
         ) v>
    /di    <
      })}               )
         </div>
         
         >div     </             </div>
                  >
      ></div        
          ntage}%` }}perceh: `${{{ widte=       styl                 -300" 
onall duratiansition-full tred-0 h-2 round-green-50assName="bg    cl               <div 
                          
 t-3">d-full h-2 mde00 roun bg-gray-2me="w-fullsNa clas<div          
                            </div>
               >
       span0}%</rate || onse_sp">{item.ret-medium="fonclassNamepan   <s             
       an> Rate</spsponseReray-600">="text-gsNamespan clas <               ">
      xt-smn tetweefy-beusti="flex jiv className     <d       >
         </div             n>
      re}</spa_scom.avg{iteum">font-medi"ame=lassN     <span c            
     </span>">Avg Scoret-gray-600ssName="texan cla       <sp          m">
     xt-sen tefy-betwesti="flex juiv className <d                  /div>
      <          span>
     ount}</m">{item.cediume="font-mlassNaspan c    <            an>
      >Posts</spgray-600"Name="text-class     <span           >
       sm"ext-between tlex justify-me="fassNa  <div cl                  ace-y-2">
me="sp classNa<div             
                    </div>
                    
        </a>            t ↗
       Visi          
               >           "
-800er:text-blue00 hov-6xs text-blueme="text-Na      class         r"
       oreferrener nperel="noo                   "
   lankarget="_b        t            ddit}`}
  {item.subrem/r/$.coddit://re={`https    href                 a
        <             </h4>
t}ddim.subreum">r/{iteediame="font-massNh4 cl     <              3">
  mb-eenjustify-betwms-center "flex ite=iv className     <d          ">
   ion-shadowtransitw-md ver:shado p-4 hounded-lgorder rosName="b{index} clas<div key=        (
        rn        retu   
       
            : 0100Count) * maxount / (item.ct > 0 ? oun = maxCge percentast       con      
  s.count))s: any) =>dits.map((op_subred.max(...tth = MamaxCount      const       {
   => : number)ny, index: amap((itembreddits. {top_su       -4">
    s-2 gapid-cols-1 md:grol"grid grid-ce=v classNam    <di
      > 0 ? (h engtts.lubreddip_s      {toe</h3>
  ormancreddit Perf">Sub-4old mbt-semiblg fonxt-sName="telas3 c       <h>
 dow-sm"d-xl p-6 shaoundeder rte borbg-whissName="  <div cla
    */}ce ts Performan Subreddinced/* Enha    {/div>

     <  )}
         e</p>
bldata availad orNo keyw-4">ter pytext-cenray-500 t-g"texsName=p clas      < : (
      )  iv>
         </d })}
     
                     )</div>
             )}
                        </div>
                     span>
</                      %
percentage}{item.trend.↘'} '↗' : ' ? === 'up'n ectiond.dir.tre   {item                    
 0'}>-60 'text-red00' :t-green-6 'tex'up' ?rection === em.trend.diit className={nd: <span     Tre             ">
    gray-500ext-xs text-"mt-2 tsName= clas<div                
    rend && (    {item.t                      
      
    v> </di              >
     ></div         
         age}%` }}nt`${perce{ width: ={ style             
        -600" over:bg-blue300 group-hration-tion-all du transiunded-full2 roue-500 h-="bg-blame  classN           
                <div             
 ll h-2">unded-fu200 roull bg-gray-e="w-fassNam   <div cl                
            >
           </div          div>
   </           n>
        rate</spa}% response  || 0ponse_rateem.respan>{it      <s                /span>
} avg score<re || 0g_sco.aviteman>{  <sp               an>
     tches</sp} mant.couempan>{it     <s                 -600">
sm text-graytext- space-x-4 ms-centeriteme="flex assNacl   <div         
           </div>                 </span>
             
          | 'unknown'}ectiveness |m.effite           {          }`}>
                         '
red-8000 text-ed-10g-r'b             
           llow-800' :text-ye00 ellow-1bg-ydium' ? 'ess === 'mem.effectiven         ite             
  0' :-green-80100 textreen-igh' ? 'bg-gss === 'hvenefecti     item.ef               l ${
    -fulndedxt-xs rou2 py-1 tex-ssName={`pla<span c                 n>
     rd}</spakeywoem.um">{itdit-mext-sm foname="ten classN <spa            
         -3">ter space-xitems-cenx Name="fle <div class           
        ">-2ween mb-betifyjusttems-center "flex iassName=div cl     <            olors">
 n-csitiotran rounded-lg y-50 p-3g-graover:be="group h classNamx}inde<div key={           (
      return      
                      * 100 : 0
/ maxCount) .count  0 ? (item maxCount >age =t percent cons             )
unt).co=> kp((k: any) ords.makeyw.top_.. = Math.max( maxCount      const         {
 number) =>ny, index:(item: aords.map(p_keyw {to        -y-4">
   cessName="spa<div cla       0 ? (
   h > gtwords.leney{top_k        
     v>
        </di
       </div>     g()}
 TimeStrinLocale).tote(new Da: {updated   Last          ">
gray-500-sm text-textame="sNv clas       <di  
 rmance</h3>eyword Perfomibold">Kg font-sext-l"teame= <h3 classN        ">
 4een mb-etw-bjustifyms-center x ite"fleassName=     <div cl
   m">shadow-s p-6 rounded-xlrder hite bo"bg-wclassName=  <div ce */}
    ormans PerfwordKeyced   {/* Enhan
    </div>

          )}
    /p>able<vail data aivityct8">No at-center py-gray-500 texe="text-am   <p classN
          ) : (>
           </div
    div>          </v>
  di    </              }
        )
    a.lengthat/ filteredD || 0), 0) c]dMetriy)[selecte((d as and) => sum + uce((sum, edta.rteredDaround(filMath.         : 
         )}%`gthredData.len, 0) / filteric] || 0)lectedMet as any)[se((d sum +  d) =>sum,ata.reduce((redDound(filte `${Math.r   ?             ' 
  rateopy_ric === 'cctedMet {selevg:  A        
      v><di      v>
        di</          }
     : maxValuealue}%`e' ? `${maxVy_ratop=== 'ctric selectedMe      Max: {     v>
              <di/div>
          <  n>
       ')}</spa', ' e('_placedMetric.re>{selectitalize"sName="capasspan cl           <>
     ic)}`}></divtedMetreclor(selricCogetMetnded-full ${-3 roume={`w-3 hsNaclas    <div    
         x-2">ter space-ex items-cenName="flssdiv cla         <
     ">t-gray-600text-sm texspace-x-6 ter justify-centems-center ame="flex isNiv clas      <d    nd */}
  art Lege Ch   {/*    
      </div>
   v>
              </di           })}
                 )
             /div>
         <   
         </div>                      e)}
ate(day.datatD       {form              nter">
   rigin-ce-45 oatesform -rot2 tran0 mt-ext-gray-50s txt-xme="tev classNa<di                             
          
     v>        </di          )}
                            iv>
        </d       
           k"></div>r-t-blacordeent btransparer-4 border- bord-1/2anslate-x -trsform2 tran1/t-ull lef-fute topame="absolclassN    <div                   div>
             </                  
   e}}%` : valu${value_rate' ? `== 'copyric =tedMetelec  {s                           >
 old"t-semibssName="fon <div cla                      /div>
     e)}<e(day.datformatDat <div>{                     ">
      p z-10-nowraacesp white-2 py-1pxs rounded -xte text text-whi1/2 bg-blackate-x-form -translanstr-2 left-1/2  mbm-fullolute botto"absName=lass   <div c                     x && (
  ndet === i{hoveredPoin                 */}
       Tooltip    {/*                  
                          /div>
      ><                '0' }}
    px' :  ? '2e > 0luHeight: va mint}%`,`${heighight: yle={{ he  st                  
              }`}            0'
      ity-6-80' : 'opacx ? 'opacityindent ===   hoveredPoi                   ${
       tion-200 duraon-all titransi-t ded rountedMetric)}lor(selecCoetMetric{`w-full ${gssName= cla                       <div
                       
   ull"> w-fs-endx item-1 fleative flexssName="rella      <div c         >
                        }
   l)int(nulveredPo => setHoseLeave={()      onMou              
  ndex)}t(iHoveredPoin> setr={() =seEnte    onMou                  ointer"
cursor-pms-center  ite-colflex flex"flex-1 =ssName   cla          
         ay.date}      key={d              
   <div             (
       rnretu                          
          0 : 0
10 * xValue) / malue> 0 ? (vamaxValue t = ighnst he       co      
      || 0c]etriedM[selecty as any) (davalue =     const             ) => {
 day, index((redData.mapilte         {f    
   -1">e-x h-full spactweenify-bed justems-en it"flexclassName=  <div            
 >ed-lg p-4"-50 roundbg-graylative h-64 assName="re    <div cl      /}
  rt *ha  {/* C
          y-4">pace-sName="s  <div clas     (
   ? ngth > 0 teredData.le     {fildiv>

    </      </div>
         /select>
          <))}
             
     ption>    </o         l}
   ben.la     {optio            ue}>
 .vallue={option} vaoption.value={<option key        (
        on => tiap(op.mOptionsRangeime          {t >
              ent"
 nsparorder-traus:boc0 fg-blue-50focus:rining-2 :rded-lg focusrounrder  botext-smy-1 me="px-3 pclassNa              lue)}
e.target.vaimeRange(ectedT => setSelChange={(e)       on
       eRange}Timtedlecue={seal         velect
        <s
         lector */}nge SeTime Ra    {/*          
        
    </div>         ))}
        >
            </button             </div>
                 >
spanabel}</.loption   <span>{           
      e)}`}></div>tion.valuopcColor(etril ${getM rounded-ful`w-2 h-2ame={v classNdi       <            e-x-1">
 nter spaccelex items-ssName="fv cla         <di        >
                
 `}   }          
     g-gray-50'er:b  : 'hov                   00'
 text-blue-7-blue-200 ue-50 borderbg-bl        ? '      
        value option.edMetric ===      select           lors ${
   nsition-coer trardl borounded-ful1 text-sm {`px-3 py-ame=lassN  c              }
  ion.value)pttedMetric(oelec setS={() => onClick                 n.value}
 key={optio            
        <button           
  tion => (ap(opions.m{metricOpt            ">
   space-x-2items-centerx e="flesNam  <div clas      
    elector */}tric S  {/* Me       >
    space-x-4"ems-centeritx e="fleam<div classN       s</h3>
   vity Trendti>Ac-semibold"xt-lg font"teme= <h3 classNa        ">
 en mb-6etwe justify-bcenters-"flex itemsName=clas   <div      ">
w-smshadop-6 ed-xl ndr rouborde harActivity Cractive  Inte    {/*  ${classNa6 space-y-assName={`<div cl   

export default AnalyticsCharts